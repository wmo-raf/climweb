function parseISO8601Duration(durationString) {
  const regex = /P(?:([0-9]+)Y)?(?:([0-9]+)M)?(?:([0-9]+)D)?(?:T(?:([0-9]+)H)?(?:([0-9]+)M)?(?:([0-9]+(?:\.[0-9]+)?)S)?)?/;
  const matches = regex.exec(durationString);

  const years = +matches[1] || 0;
  const months = +matches[2] || 0;
  const days = +matches[3] || 0;
  const hours = +matches[4] || 0;
  const minutes = +matches[5] || 0;
  const seconds = parseFloat(matches[6]) || 0;

  const duration =
    (((years * 365 + months * 30 + days) * 24 + hours) * 60 + minutes) * 60 +
    seconds;
  return duration * 1000; // ms
}

function extractPlaceholders(url) {
  const matches = url.match(/{\w+}/g);
  return matches ? matches.map(m => m.replace(/[{}]/g, "")) : [];
}

// 2. Build params object from selectors and context
function buildParams(placeholders, paramsSelectorConfig, containerId, context = {}) {
  const params = { ...context };

  paramsSelectorConfig.forEach(param => {
    if (param.key === "time") return; // Skip time, handled by calendar
    const select = document.getElementById(`param-${param.key}`);
    if (select && placeholders.includes(param.key)) {
      params[param.key] = select.value;
    }
  });
  return params;
}



function getValidTimestamps(rangeString) {
  const [start, end, durationStr] = rangeString.split("/");
  const startTime = new Date(start).getTime();
  const endTime = new Date(end).getTime();
  const duration = parseISO8601Duration(durationStr);

  const timestamps = [];
  for (let t = startTime; t < endTime; t += duration) {
    timestamps.push(new Date(t).toISOString());
  }
  return timestamps;
}



async function getTimeValuesFromWMS(wmsUrl, layerName, params = {}) {
  const defaultParams = {
    service: "WMS",
    request: "GetCapabilities",
    version: "1.3.0",
  };
  const queryParams = new URLSearchParams({ ...defaultParams, ...params }).toString();
  const fullUrl = `${wmsUrl}?${queryParams}`;

  try {
    const xmlText = await fetch(fullUrl).then((res) => res.text());
    const xml = new DOMParser().parseFromString(xmlText, "application/xml");
    const layers = xml.querySelectorAll("Layer");
    let match = null;

    layers.forEach((layer) => {
      const nameEl = layer.querySelector("Name");
      if (nameEl && nameEl.textContent === layerName) match = layer;
    });

    if (!match) return [];

    const dimension = match.querySelector("Dimension[name='time']");
    const timeValueStr = dimension ? dimension.textContent : "";
    const dateRange = timeValueStr.split("/");

    if (dateRange.length > 1) {
      const isoDuration = dateRange[dateRange.length - 1];
      const durationDays = parseISO8601Duration(isoDuration) / 8.64e7;
      if (durationDays < 1) {
        const endTime = new Date(dateRange[1]);
        const startTime = new Date(endTime.getTime() - 2 * 86400000);
        return getValidTimestamps(`${startTime.toISOString()}/${endTime.toISOString()}/${isoDuration}`);
      }
      return getValidTimestamps(timeValueStr);
    }
    return timeValueStr.split(",");
  } catch (error) {
    console.error(`Error fetching or parsing GetCapabilities document: ${error.message}`);
    return [];
  }
}
function getTimeFromList(timestamps, method) {
  if (!timestamps.length) return null;
  switch (method) {
    case "next_to_now":
      return getNextToNowDate(timestamps) || timestamps[timestamps.length - 1];
    case "previous_to_now":
      return getPreviousToNowDate(timestamps) || timestamps[timestamps.length - 1];
    case "latest_from_source":
      return timestamps[timestamps.length - 1];
    case "earliest_from_source":
      return timestamps[0];
    default:
      return timestamps[timestamps.length - 1];
  }
}

(function () {
  const datasets = {}
  const layerConfigs = {}
  const datepickerInstances = {};
  const mapInstances = {};

  const containers = document.querySelectorAll(".map-container");

  const { datasetsUrl, countryBounds, boundaryTilesUrl } = mapConfig() || {};
  console.log("datasetsUrl",datasetsUrl)
  const dashboardBasemapStyle = {
    version: 8,
    sources: {
      "carto-dark": {
        type: "raster",
        tiles: [
          "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
          "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
          "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
          "https://d.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
        ],
        tileSize: 256,
      },
    },
    layers: [
      {
        id: "carto-dark",
        source: "carto-dark",
        type: "raster",
        minzoom: 0,
        maxzoom: 22,
      },
    ],
  };



  function initializeMap() {

    containers.forEach((container) => {

      const tileJsonUrl = container.dataset.tilejson;
      const layerType = container.dataset.layerType;
      const displayFormat = container.dataset.dateFormat
      const containerId = container.id;
      const selected_dataset = container.dataset.dataset
      const selected_layer = container.dataset.layer
      const admin_path = container.dataset.gid0 + (container.dataset.gid1 ? `/${container.dataset.gid1}` : '') + (container.dataset.gid2 ? `/${container.dataset.gid2}` : '')
      const mapType = container.dataset.mapType


      if (!containerId || !tileJsonUrl || !layerType) return;

      createMap(containerId, selected_layer, selected_dataset, layerType, admin_path, displayFormat, mapType);


    });
  }

  function updateMapLayerWithDate(containerId, selectedDateTime) {
    const mapInstance = mapInstances[containerId];
    const layerConfig = layerConfigs[containerId];

    if (!mapInstance || !layerConfig) {
      console.error(`Map or layerConfig not found for containerId: ${containerId}`);
      return;
    }

    updateMapLayer(mapInstance, layerConfig, selectedDateTime);
  }


  // Initialize Datepicker for all containers
  function initializeCalendar() {
    containers.forEach((container) => {
      const containerId = container.id;
      const inputEl = document.querySelector(`#mapdate-${containerId}`);
      const timeSelectEl = document.querySelector(`#maptime-${containerId}`); // Time dropdown

      if (!inputEl) {
        console.error(`Date input not found for containerId: ${containerId}`);
        return;
      }

      // Determine the date format
      const dateFormat = container.dataset.dateFormat || "yyyy-MM-dd HH:mm";
      let dpFormat = "yyyy-mm-dd"; // Default format
      let pickLevel = 0;

      switch (dateFormat) {
        case "yyyy":
          dpFormat = "yyyy";
          pickLevel = 2; // Year picker
          break;
        case "yyyy-MM":
          dpFormat = "yyyy-mm";
          pickLevel = 1; // Month picker
          break;
        case "yyyy-MM-dd":
          dpFormat = "yyyy-mm-dd";
          pickLevel = 0; // Full date picker
          break;
        case "yyyy-MM-dd HH:mm":
          dpFormat = "yyyy-mm-dd"; // Date only (time handled separately)
          pickLevel = 0;
          break;
      }

      // Initialize the datepicker
      const datepicker = new Datepicker(inputEl, {
        format: dpFormat,
        autohide: true,
        todayHighlight: true,
        clearBtn: true,
        pickLevel,
      });

      datepickerInstances[containerId] = datepicker;

      // Handle date and time changes
      const handleDateTimeChange = () => {
        const selectedDate = datepicker.getDate();
        const selectedTime = timeSelectEl ? timeSelectEl.value : "00:00";

        if (selectedDate) {
          // Combine date and time into a single ISO string
          const [hours, minutes] = selectedTime.split(":").map(Number);
          selectedDate.setHours(hours || 0, minutes || 0, 0, 0);
          const isoDateTime = selectedDate.toISOString();
          updateMapLayerWithDate(containerId, isoDateTime);
        }
      };

      // Add event listeners for date and time changes
      inputEl.addEventListener("changeDate", handleDateTimeChange);
      if (timeSelectEl) {
        timeSelectEl.addEventListener("change", handleDateTimeChange);
      }
    });
  }

  function setCalendarDates(containerId, availableDates, displayFormat) {
    return new Promise((resolve) => {
      const picker = datepickerInstances[containerId];
      const timeSelectEl = document.querySelector(`#maptime-${containerId}`);

      if (!picker || !availableDates?.length) return resolve();

      const parsedDates = availableDates.map((d) => new Date(d)).filter((d) => !isNaN(d));
      if (!parsedDates.length) return resolve();

      const latestDate = new Date(Math.max(...parsedDates)); // Get the latest date

      const availableDatesSet = new Set(
        availableDates.map((date) => {
          // Create a new Date object and reset the time to midnight (00:00:00)
          const dateWithoutTime = new Date(date);
          dateWithoutTime.setHours(0, 0, 0, 0);
          return formatDateTimeJS(dateWithoutTime, displayFormat);
        })
      );

      // Function to check if a date is available
      const isDateAvailable = (date) => {
        // Ensure the input date also has its time stripped
        const dateWithoutTime = new Date(date);
        dateWithoutTime.setHours(0, 0, 0, 0);
        const formattedDate = formatDateTimeJS(dateWithoutTime, displayFormat);

        return availableDatesSet.has(formattedDate);
      };

      picker.setDate(latestDate);

      picker.setOptions({
        beforeShowDay: (date) => {
          return isDateAvailable(date) ? { enabled: true } : { enabled: false };
        },
        beforeShowYear: (date) => {
          return isDateAvailable(date) ? { enabled: true } : { enabled: false };
        },
        beforeShowMonth: (date) => {
          return isDateAvailable(date) ? { enabled: true } : { enabled: false };
        },
      });

      if (timeSelectEl) {
        // Function to update available times for the selected date
        const updateAvailableTimes = (selectedDate) => {

          const availableTimes = parsedDates.filter(d =>
            new Date(d).getFullYear() === new Date(selectedDate).getFullYear() &&
            new Date(d).getMonth() === new Date(selectedDate).getMonth() &&
            new Date(d).getDate() === new Date(selectedDate).getDate()
          )
            .sort((a, b) => a - b)
            .map((d) => {
              const hours = d.getHours().toString().padStart(2, "0");
              const minutes = d.getMinutes().toString().padStart(2, "0");
              return `${hours}:${minutes}`;
            });

          // Populate the time dropdown
          timeSelectEl.innerHTML = availableTimes
            .map((time) => `<option value="${time}">${time}</option>`)
            .join("");

          // Set the default time to the latest available time
          if (availableTimes.length) {
            timeSelectEl.value = availableTimes[availableTimes.length - 1];
          }
        };

        // Update times for the latest date initially
        updateAvailableTimes(latestDate);

        // Add event listener to update times when the date changes
        picker.inputField.addEventListener("changeDate", (ev) => {
          const selectedDate = ev.detail.date;
          if (selectedDate) {
            updateAvailableTimes(selectedDate);
          }
        });
      }

      resolve();
    });
  }

  function createMap(containerId, selected_layer, selected_dataset, layerType, admin_path, displayFormat, mapType) {

    // Clean up if a map already exists for this container
    if (mapInstances[containerId]) {
      console.warn(`Removing existing map for ${containerId} to free WebGL context.`);
      mapInstances[containerId].remove();
      delete mapInstances[containerId];
    }
    const isBefore = containerId.startsWith('before-');
    const isAfter = containerId.startsWith('after-');


    if (mapType === "single" && !isBefore && !isAfter) {
      // Single map logic
      map = new maplibregl.Map({
        container: containerId,
        style: dashboardBasemapStyle,
        scrollZoom: false,
      });

      mapInstances[containerId] = map;

      updateLayer(map, containerId, selected_layer, selected_dataset, layerType, displayFormat);

      map.addControl(new maplibregl.NavigationControl({ showCompass: false }));
      map.addControl(new maplibregl.FullscreenControl());

      loadBoundaries(map, admin_path);


      return;

    }
    if (mapType === "comparison") {
      const compareContainer = `#comparison-${containerId}`.replace('before-', '').replace('after-', '');


      // Handle 'before' map
      if (isBefore) {
        const mapBefore = new maplibregl.Map({
          container: containerId,
          style: dashboardBasemapStyle,
          scrollZoom: false,

        });

        mapInstances[containerId] = mapBefore;

        mapBefore.on("load", () => {
          updateLayer(mapBefore, containerId, selected_layer, selected_dataset, layerType, displayFormat);
          loadBoundaries(mapBefore, admin_path);
        });

        // If 'after' already exists, initialize compare
        const afterId = containerId.replace('before-', 'after-');
        if (mapInstances[afterId]) {
          new maplibregl.Compare(mapBefore, mapInstances[afterId], compareContainer, {
            orientation: "vertical",
          });
        }
      }


      // Handle 'after' map
      if (isAfter) {
        const mapAfter = new maplibregl.Map({
          container: containerId,
          style: dashboardBasemapStyle,
          scrollZoom: false,

        });
        mapInstances[containerId] = mapAfter;

        mapAfter.on("load", () => {
          updateLayer(mapAfter, containerId, selected_layer, selected_dataset, layerType, displayFormat);
          loadBoundaries(mapAfter, admin_path);
        });

        // If 'before' already exists, initialize compare
        const beforeId = containerId.replace('after-', 'before-');
        if (mapInstances[beforeId]) {
          new maplibregl.Compare(mapInstances[beforeId], mapAfter, compareContainer, {
            orientation: "vertical",
          });
        }

        return;
      }

    }


  }


  async function getLayerDataset(selected_layer,selected_dataset) {
    if (typeof datasetsUrl !== "undefined" && selected_dataset && selected_layer) {
      if (datasets[selected_dataset]) return datasets[selected_dataset];
      const dataset = await fetch(datasetsUrl + selected_dataset).then(res => res.json());
      datasets[selected_dataset] = dataset;
      return dataset;
    }
  }

  function updateTileUrl(tileUrl, params) {
    const url = new URL(tileUrl);
    const qs = new URLSearchParams(url.search);
    Object.keys(params).forEach(key => qs.set(key, params[key]));
    url.search = decodeURIComponent(qs);
    return decodeURIComponent(url.href);
  }

  function updateMapLayer(map, layerConfig, withDate, tileUrlOverride) {
    const { source: { id: sourceId }, layer: { id: layerId }, layerType } = layerConfig;
    if (map.getLayer(layerId)) map.removeLayer(layerId);
    if (map.getSource(sourceId)) map.removeSource(sourceId);

    const tileUrl = tileUrlOverride || updateTileUrl(layerConfig.source.tiles, { time: withDate });

    if (["raster_file", "wms", "raster_tile"].includes(layerType)) {
      map.addSource(sourceId, { type: "raster", tiles: [tileUrl], tileSize: 256 });
      map.addLayer({ id: layerId, type: "raster", source: sourceId });
    } else if (layerType === "vector_tile") {
      map.addSource(sourceId, { type: "vector", tiles: [tileUrl] });
      map.addLayer({
        id: layerId,
        type: "fill",
        source: sourceId,
        "source-layer": "default",
        paint: { "fill-color": "#088", "fill-opacity": 0.6 },
      });
    }
    if (map.getLayer("admin-boundary-line") && map.getLayer("admin-boundary-line-2")) {
      map.moveLayer("admin-boundary-line");
      map.moveLayer("admin-boundary-line-2");
    }
  }

  function setParamSelectors(containerID, paramsSelectorConfig, layerConfigs, map) {
    const paramsContainer = document.getElementById(`paramsContainer-${containerID}`);
    paramsContainer.innerHTML = ''; // Clear any previous content

    let hasOptions = false;

    paramsSelectorConfig.forEach((param) => {
      if (!param.options || param.key === "time") return; // skip time, handled by calendar

      hasOptions = true;

      const wrapper = document.createElement('div');
      wrapper.classList.add('param-group', 'select', 'is-small');

      const label = document.createElement('label');
      label.textContent = param.label || param.key;
      label.setAttribute('for', `param-${param.key}`);

      const select = document.createElement('select');
      select.id = `param-${param.key}`;
      select.dataset.key = param.key;

      select.innerHTML = param.options
        .map(option => `<option value="${option.value}" ${option.default ? "selected" : ""}>${option.label}</option>`)
        .join('');

      // select.value = param.default_value || param.options[0]?.value || '';

      select.addEventListener('change', () => {
        updateLayerWithParams(containerID, map, layerConfigs);
      });

      wrapper.appendChild(label);
      wrapper.appendChild(select);
      paramsContainer.appendChild(wrapper);
    });

    paramsContainer.style.display = hasOptions ? 'block' : 'none';
  }

  function getLayerConfig(layer, tileUrl, containerId) {
    const config = {
      layerType: layer.layerType,
      source: { id: layer.id, type: "raster", tiles: [tileUrl] },
      layer: { id: layer.id, type: "raster" },
      paramsSelectorConfig: layer.paramsSelectorConfig || []

    };
    layerConfigs[containerId] = config;
    return config;
  }

  async function getLayerDates(url) {
    const res = await fetch(url);
    const res_1 = await res.json();
    return res_1.timestamps;
  }

  function createSvgChoroplethLegend(
    color,
    {
      title,
      tickSize = 6,
      width = 240,
      height = 44 + tickSize,
      marginTop = 18,
      marginRight = 0,
      marginBottom = 16 + tickSize,
      marginLeft = 0,
      ticks = width / 64,
      tickFormat,
      tickValues,
      strokeColor = "rgba(0,0,0,.15)",
    } = {}
  ) {
    function ramp(color, n = 256) {
      const canvas = document.createElement("canvas");
      canvas.width = n;
      canvas.height = 1;
      const context = canvas.getContext("2d");
      for (let i = 0; i < n; ++i) {
        context.fillStyle = color(i / (n - 1));
        context.fillRect(i, 0, 1, 1);
      }
      return canvas;
    }

    const svg = d3.create("svg")
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [0, 0, width, height])
      .style("overflow", "visible")
      .style("display", "block");

    let tickAdjust = (g) =>
      g.selectAll(".tick line").attr("y1", marginTop + marginBottom - height);
    let x;

    // Continuous
    if (color.interpolate) {
      const n = Math.min(color.domain().length, color.range().length);

      x = color
        .copy()
        .rangeRound(d3.quantize(d3.interpolate(marginLeft, width - marginRight), n));

      svg
        .append("image")
        .attr("x", marginLeft)
        .attr("y", marginTop)
        .attr("width", width - marginLeft - marginRight)
        .attr("height", height - marginTop - marginBottom)
        .attr("preserveAspectRatio", "none")
        .attr(
          "xlink:href",
          ramp(color.copy().domain(d3.quantize(d3.interpolate(0, 1), n))).toDataURL()
        );
    }

    // Sequential
    else if (color.interpolator) {
      x = Object.assign(
        color
          .copy()
          .interpolator(d3.interpolateRound(marginLeft, width - marginRight)),
        {
          range() {
            return [marginLeft, width - marginRight];
          },
        }
      );

      svg
        .append("image")
        .attr("x", marginLeft)
        .attr("y", marginTop)
        .attr("width", width - marginLeft - marginRight)
        .attr("height", height - marginTop - marginBottom)
        .attr("preserveAspectRatio", "none")
        .attr("xlink:href", ramp(color.interpolator()).toDataURL());

      // scaleSequentialQuantile doesn’t implement ticks or tickFormat.
      if (!x.ticks) {
        if (tickValues === undefined) {
          const n = Math.round(ticks + 1);
          tickValues = d3.range(n).map((i) => d3.quantile(color.domain(), i / (n - 1)));
        }
        if (typeof tickFormat !== "function") {
          tickFormat = format(tickFormat === undefined ? ",f" : tickFormat);
        }
      }
    }

    // Threshold
    else if (color.invertExtent) {
      const thresholds = color.thresholds
        ? color.thresholds() // scaleQuantize
        : color.quantiles
          ? color.quantiles() // scaleQuantile
          : color.domain(); // scaleThreshold

      const thresholdFormat =
        tickFormat === undefined
          ? (d) => d
          : typeof tickFormat === "string"
            ? format(tickFormat)
            : tickFormat;

      x = d3.scaleLinear()
        .domain([-1, color.range().length - 1])
        .rangeRound([marginLeft, width - marginRight]);

      svg
        .append("g")
        .selectAll("rect")
        .data(color.range())
        .join("rect")
        .attr("x", (d, i) => x(i - 1))
        .attr("y", marginTop)
        .attr("width", (d, i) => x(i) - x(i - 1))
        .attr("height", height - marginTop - marginBottom)
        .attr("fill", (d) => d)
        .attr("stroke", strokeColor);

      tickValues = d3.range(thresholds.length);
      tickFormat = (i) => thresholdFormat(thresholds[i], i);
    }

    // Ordinal
    else {
      x = d3.scaleBand()
        .domain(color.domain())
        .rangeRound([marginLeft, width - marginRight]);

      svg
        .append("g")
        .selectAll("rect")
        .data(color.domain())
        .join("rect")
        .attr("x", x)
        .attr("y", marginTop)
        .attr("width", Math.max(0, x.bandwidth() - 1))
        .attr("height", height - marginTop - marginBottom)
        .attr("fill", color)
        .attr("stroke", strokeColor);

      tickAdjust = () => {
      };
    }

    svg
      .append("g")
      .attr("transform", `translate(0,${height - marginBottom})`)
      .call(
        d3.axisBottom(x)
          .ticks(ticks, typeof tickFormat === "string" ? tickFormat : undefined)
          .tickFormat(typeof tickFormat === "function" ? tickFormat : undefined)
          .tickSize(tickSize)
          .tickValues(tickValues)
      )
      .call(tickAdjust)
      .call((g) => g.select(".domain").remove())
      .call((g) =>
        g
          .append("text")
          .attr("x", marginLeft)
          .attr("y", marginTop + marginBottom - height - 6)
          .attr("fill", "currentColor")
          .attr("text-anchor", "start")
          .attr("font-weight", "bold")
          .attr("class", "title")
          .text(title)
      );

    return svg.node();
  }


  function createLegend(legendConfig) {
    const { items, ...rest } = legendConfig;
    if (items?.length) {
      const thresholds = items.map(item => item.from || item.name);
      const colors = items.map(item => item.color);
      return createSvgChoroplethLegend(d3.scaleThreshold(thresholds, colors), { tickSize: 0, ...rest });
    }
    return null;
  }

  function updateLayer(map, containerId, selected_layer, selected_dataset, layerType, displayFormat) {
    getLayerDataset(selected_layer, selected_dataset).then(async activeLayerDataset => {

      if (!activeLayerDataset) return;
      const layer = activeLayerDataset.layers?.[0];
      const { tileJsonUrl, getCapabilitiesLayerName, getCapabilitiesUrl, paramsSelectorConfig, layerConfig, currentTimeMethod, legendConfig } = layer;
      let layerDates, tileUrl, layerSetup;

      if (["raster_file", "raster_tile", "vector_tile"].includes(layerType)) {
        const timestamps = await getLayerDates(tileJsonUrl);
        layerDates = timestamps.sort((a, b) => new Date(b) - new Date(a));
        const defaultDate = layerDates?.[0];
        const isoString = new Date(defaultDate).toISOString();
        tileUrl = updateTileUrl(layer.layerConfig.source.tiles[0], { time: isoString })
        layerSetup = getLayerConfig(layer, tileUrl, containerId);

        if (layerType === "raster_tile" || layerType === "vector_tile") {

          setParamSelectors(containerId, paramsSelectorConfig, layerSetup, map)

          const placeholders = extractPlaceholders(tileUrl);

          // Build params from selectors
          const params = buildParams(placeholders, paramsSelectorConfig, containerId, {
            // Add any context params here, e.g. geostore_id if available
            geostore_id: window.geostoreId || undefined
          });
          Object.keys(params).forEach(key => {
            tileUrl = tileUrl.replace(`{${key}}`, params[key]);
          });
        }

        layerSetup = getLayerConfig(layer, tileUrl, containerId);

      } else if (layerType === "wms") {
        const timestamps = await getTimeValuesFromWMS(getCapabilitiesUrl, getCapabilitiesLayerName);
        layerDates = timestamps.sort((a, b) => new Date(b) - new Date(a));
        const currentLayerTime = getTimeFromList([...layerDates], currentTimeMethod);
        const timeSelectorConfig = paramsSelectorConfig.find(c => c.key === "time");
        if (timeSelectorConfig) {
          let timeUrlParam = timeSelectorConfig.url_param || "time";
          tileUrl = updateTileUrl(layerConfig.source.tiles[0], { [timeUrlParam]: currentLayerTime });
        }
        layerSetup = getLayerConfig(layer, tileUrl, containerId);

      }

      if (legendConfig?.items?.length) {
        const legend = createLegend(legendConfig);
        $("#legend-" + containerId).html(legend).show();
      }

      setCalendarDates(containerId, layerDates, displayFormat).then(() => {
        const picker = datepickerInstances[containerId];
        const input = document.querySelector(`#mapdate-${containerId}`);

        if (!picker || !input) return;

        input.addEventListener("changeDate", (ev) => {
          const selectedDate = ev.detail.date;
          if (selectedDate) {
            const dateStrIso = new Date(selectedDate).toISOString();
            updateMapLayer(map, layerSetup, dateStrIso);
          }
        });
      });

      const defaultDate = layerDates?.[0];
      updateMapLayer(map, layerSetup, defaultDate);

    }).catch(console.log);
  }


  function loadBoundaries(map, admin_path) {
    fetch(`/api/geostore/admin/${admin_path}?thresh=0.005`)
      .then(res => res.json())
      .then((geostoreInfo) => {
        const { geojson, bbox } = geostoreInfo.attributes;
        if (geojson && bbox) {
          map.fitBounds(bbox, { padding: 30 });
          map.addSource("admin-boundary-source", { type: "geojson", data: geojson });
          map.addLayer({
            id: 'admin-boundary-line',
            type: 'line',
            source: 'admin-boundary-source',
            paint: { "line-color": "#C0FF24", "line-width": 1, "line-offset": 1 }
          });
          map.addLayer({
            id: 'admin-boundary-line-2',
            type: 'line',
            source: 'admin-boundary-source',
            paint: { "line-color": "#000", "line-width": 1.5 }
          });
        } else {
          if (typeof countryBounds !== 'undefined' && countryBounds) {
            const bounds = [[countryBounds[0], countryBounds[1]], [countryBounds[2], countryBounds[3]]];
            map.fitBounds(bounds, { padding: 50 });
          }
          if (typeof boundaryTilesUrl !== 'undefined' && boundaryTilesUrl) {
            map.addSource("admin-boundary-source", { type: "vector", tiles: [boundaryTilesUrl] });
            ["admin-boundary-line", "admin-boundary-line-2"].forEach((id, i) => {
              map.addLayer({
                id,
                type: 'line',
                source: 'admin-boundary-source',
                "source-layer": "default",
                "filter": ["==", "level", 0],
                paint: {
                  "line-color": i === 0 ? "#C0FF24" : "#000",
                  "line-width": i === 0 ? 1 : 1.5,
                  ...(i === 0 ? { "line-offset": 1 } : {})
                }
              });
            });
          }
        }
      });
  }

  function getSelectedParams(paramsSelectorConfig) {
    const params = {};
    paramsSelectorConfig.forEach(param => {
      if (param.key === "time") return;
      const select = document.getElementById(`param-${param.key}`);
      if (select) params[param.key] = select.value;
    });
    return params;
  }

  function updateLayerWithParams(containerID, map, layerConfigs) {
    const paramsSelectorConfig = layerConfigs?.paramsSelectorConfig || [];
    const params = getSelectedParams(paramsSelectorConfig);

    const picker = datepickerInstances[containerID];
    let time = null;

    if (picker && picker.getDate()) {
      time = new Date(picker.getDate()).toISOString();
    }

    if (time) params.time = time;

    let tileUrl = layerConfigs.source.tiles[0];
    Object.keys(params).forEach((key) => {
      tileUrl = tileUrl.replace(`{${key}}`, params[key]);
    });

    updateMapLayer(map, layerConfigs, time, tileUrl);
  }

  initializeMap()
  initializeCalendar()
  function destroyMap(containerId) {
    const map = mapInstances[containerId];
    if (map && map.remove) {
      console.log(`Removing map for ${containerId}`);
      map.remove();
      delete mapInstances[containerId];
    }
  }

  // === LAZY LOAD MAPS ===
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const containerId = entry.target.id;

        if (entry.isIntersecting) {
          // Avoid re-initializing existing maps
          if (!mapInstances[containerId]) {
            console.log(`Initializing map for ${containerId}`);
            const mapType = entry.target.dataset.mapType || 'normal'; // optional attribute
            const selected_layer = entry.target.dataset.layer || null;
            const selected_dataset = entry.target.dataset.dataset || null;
            const layerType = entry.target.dataset.layerType || null;
            const displayFormat = entry.target.dataset.displayFormat || null;
            const admin_path = entry.target.dataset.adminPath || null;

            createMap(containerId, mapType, selected_layer, selected_dataset, layerType, displayFormat, admin_path);
          }

          observer.unobserve(entry.target);
        }
      });
    },
    {
      root: null,
      rootMargin: '0px',
      threshold: 0.1, // load when 10% visible
    }
  );

  // Observe all map containers
  document.querySelectorAll('.map-container').forEach((el) => observer.observe(el));
})()

