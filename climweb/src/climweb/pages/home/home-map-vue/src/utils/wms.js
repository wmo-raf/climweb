import WMSCapabilities from "wms-capabilities";
import {subDays} from "date-fns";

function parseISO8601Duration(durationString) {
    const regex =
        /P(?:([0-9]+)Y)?(?:([0-9]+)M)?(?:([0-9]+)D)?(?:T(?:([0-9]+)H)?(?:([0-9]+)M)?(?:([0-9]+(?:\.[0-9]+)?)S)?)?/;
    const matches = regex.exec(durationString);

    const years = matches[1] || 0;
    const months = matches[2] || 0;
    const days = matches[3] || 0;
    const hours = matches[4] || 0;
    const minutes = matches[5] || 0;
    const seconds = parseFloat(matches[6]) || 0;

    const duration =
        (((years * 365 + months * 30 + days) * 24 + hours) * 60 + minutes) * 60 +
        seconds;
    return duration * 1000; // convert to milliseconds
}

function getValidTimestamps(rangeString) {
    const parts = rangeString.split("/");
    const start_time = new Date(parts[0]);
    const end_time = new Date(parts[1]);
    const duration = parseISO8601Duration(parts[2]);

    let current_time = start_time.getTime();
    const valid_timestamps = [];

    while (current_time < end_time.getTime()) {
        valid_timestamps.push(new Date(current_time).toISOString());
        current_time += duration;
    }

    return valid_timestamps;
}

/**
 * Build the GetCapabilities url. The configured url may already carry WMS parameters
 * (e.g. ...?SERVICE=WMS&REQUEST=GetCapabilities), so existing service/request/version parameters
 * are replaced, whatever their case, rather than appended a second time
 */
export const buildCapabilitiesUrl = (wmsUrl, params = {}) => {
    const defaultParams = {
        service: "WMS",
        request: "GetCapabilities",
        version: "1.3.0",
        ...params,
    };

    const url = new URL(wmsUrl, window.location.href);
    const overridden = Object.keys(defaultParams).map(key => key.toLowerCase());

    for (const key of [...url.searchParams.keys()]) {
        if (overridden.includes(key.toLowerCase())) {
            url.searchParams.delete(key);
        }
    }

    for (const [key, value] of Object.entries(defaultParams)) {
        url.searchParams.set(key, value);
    }

    return url.toString();
};

/**
 * Find a layer by name anywhere in the capabilities layer tree. Layers can sit directly under
 * Capability.Layer, or be nested deeper, e.g. in layer groups
 */
const findLayer = (layer, layerName) => {
    if (!layer) {
        return null;
    }

    const layers = Array.isArray(layer) ? layer : [layer];

    for (const l of layers) {
        if (l.Name === layerName) {
            return l;
        }
        const match = findLayer(l.Layer, layerName);
        if (match) {
            return match;
        }
    }

    return null;
};

export const getTimeValuesFromWMS = async (wmsUrl, layerName, params = {}) => {
    try {
        // Fetch the GetCapabilities document from the WMS server
        const xmlText = await fetch(buildCapabilitiesUrl(wmsUrl, params)).then(res => res.text());

        // parse xml
        const capabilities = new WMSCapabilities(xmlText).toJSON();

        const match = findLayer(capabilities?.Capability?.Layer, layerName);

        if (!match) {
            console.warn(`WMS layer "${layerName}" not found in GetCapabilities document`);
            return [];
        }

        // get time values. Layers without a time dimension have none
        const dimensions = Array.isArray(match.Dimension) ? match.Dimension : [];
        const timeValueStr = (dimensions.find((d) => d.name === "time")?.values || "").trim();

        if (!timeValueStr) {
            return [];
        }

        let dateRange = timeValueStr.split("/");

        if (!!dateRange.length && dateRange.length > 1) {
            const isoDuration = dateRange[dateRange.length - 1];
            const durationMilliseconds = parseISO8601Duration(isoDuration);
            const durationDays = durationMilliseconds / 8.64e7;

            // if the interval is less that 24 hours, by default return dates for the past one month only.
            // This is a quick implementation to avoid the browser hanging.
            // In future we can implement this with web workers to show all the dates
            if (durationDays < 1) {
                const endTime = new Date(dateRange[1]);
                const startTime = subDays(endTime, 2);

                return getValidTimestamps(
                    `${startTime.toISOString()}/${endTime.toISOString()}/${isoDuration}`
                );
            }

            return getValidTimestamps(timeValueStr);
        }

        return timeValueStr.split(",").map(value => value.trim()).filter(Boolean)
    } catch (error) {
        console.error(
            `Error fetching or parsing GetCapabilities document: ${error.message}`
        );
        return [];
    }
};
