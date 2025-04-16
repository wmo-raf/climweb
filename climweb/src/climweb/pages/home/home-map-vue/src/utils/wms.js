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

export const getTimeValuesFromWMS = async (wmsUrl, layerName, params = {}) => {
    const defaultParams = {
        service: "WMS",
        request: "GetCapabilities",
        version: "1.3.0",
    };

    const queryParams = new URLSearchParams({...defaultParams, ...params}).toString();
    const fullUrl = `${wmsUrl}?${queryParams}`;

    try {
        // Fetch the GetCapabilities document from the WMS server
        const xmlText = await fetch(fullUrl).then(res => res.text());

        // parse xml
        const capabilities = new WMSCapabilities(xmlText).toJSON();

        // get all layers
        const layers = capabilities?.Capability?.Layer?.Layer || [];

        // find matching layer by name
        const match = layers.find((l) => l.Name === layerName) || {};

        // get time values
        const timeValueStr =
            match?.Dimension?.find((d) => d.name === "time")?.values || [];

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

        const timestamps = timeValueStr.split(",");

        // sort
        return timestamps && timestamps.sort((a, b) => new Date(a) - new Date(b));
    } catch (error) {
        console.error(
            `Error fetching or parsing GetCapabilities document: ${error.message}`
        );
        return [];
    }
};