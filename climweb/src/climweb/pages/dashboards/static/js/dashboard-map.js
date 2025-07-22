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
    const parser = new DOMParser();
    const xml = parser.parseFromString(xmlText, "application/xml");

    const layers = xml.querySelectorAll("Layer");
    let match = null;

    layers.forEach((layer) => {
      const nameEl = layer.querySelector("Name");
      if (nameEl && nameEl.textContent === layerName) {
        match = layer;
      }
    });

    if (!match) return [];

    const dimension = match.querySelector("Dimension[name='time']");
    const timeValueStr = dimension ? dimension.textContent : "";
    const dateRange = timeValueStr.split("/");

    if (!!dateRange.length && dateRange.length > 1) {
      const isoDuration = dateRange[dateRange.length - 1];
      const durationMilliseconds = parseISO8601Duration(isoDuration);
      const durationDays = durationMilliseconds / 8.64e7;

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

function getTimeFromList(timestamps, currentTimeMethod) {
    let currentTime = timestamps[timestamps.length - 1];

    switch (currentTimeMethod) {
        case "next_to_now":
            const nextDate = getNextToNowDate(timestamps);
            if (nextDate) {
                currentTime = nextDate;
            }
            break;
        case "previous_to_now":
            const previousDate = getPreviousToNowDate(timestamps);
            if (previousDate) {
                currentTime = previousDate;
            }
            break;
        case "latest_from_source":
            currentTime = timestamps[timestamps.length - 1];
            break;
        case "earliest_from_source":
            currentTime = timestamps[0];
            break;
        default:
            break;
    }

    return currentTime;
};


(function () {
  const datasets = {}
  const layerConfigs = {}
  const slider = $(".layer-date-slider")

  const { datasetsUrl, countryBounds, boundaryTilesUrl } = mapConfig()
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
    const containers = document.querySelectorAll(".map-container");

    containers.forEach((container) => {

      const tileJsonUrl = container.dataset.tilejson;
      const layerType = container.dataset.layerType;
      const containerId = container.id;
      const selected_dataset = container.dataset.dataset
      const selected_layer = container.dataset.layer

      if (!containerId || !tileJsonUrl || !layerType) return;

      createMap(containerId, selected_layer, selected_dataset,layerType );
    });
  }


  function createMap(containerId,selected_layer, selected_dataset, layerType) {


    const map = new maplibregl.Map({
      container: containerId,
      style: dashboardBasemapStyle,
      scrollZoom: false
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }));
    map.addControl(
      new maplibregl.AttributionControl({
        customAttribution:
          '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        compact: true,
      })
    );
    map.addControl(new maplibregl.FullscreenControl());

    map.on("load", () => {

      updateLayer(map, containerId, selected_dataset, selected_layer, layerType)
      loadBoundaries(map)


    });

  }

  function tsToDate(ts) {
    const d = new Date(ts);
    const lang = "en-US";

    return d.toLocaleDateString(lang, {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  const onDateChange = (map, selectedDate, layerId) => {
    const { from_value } = selectedDate
    const isoString = new Date(from_value).toISOString()

    const layerConfig = layerConfigs[layerId]

    if (layerConfig) {
      updateSourceTileUrl(map, layerConfig.source.id, { time: isoString })
    }
  }

  const updateSourceTileUrl = (map, sourceId, params) => {

    // Get the source object from the map using the specified source ID.
    const source = map.getSource(sourceId);
    const sourceTileUrl = source.tiles[0]
    const newTileUrl = updateTileUrl(sourceTileUrl, params)

    // Replace the source's tile URL with the updated URL.
    map.getSource(sourceId).tiles = [newTileUrl];

    // Remove the tiles for the updated source from the map cache.
    map.style.sourceCaches[sourceId].clearTiles();

    // Load the new tiles for the updated source within the current viewport.
    map.style.sourceCaches[sourceId].update(map.transform);

    // Trigger a repaint of the map to display the updated tiles.
    map.triggerRepaint();
  }

  const updateSlider = (map, dateValues, layerId) => {
    const dateSlider = slider.data("ionRangeSlider");

    if (dateSlider) {
      // destroy  existing  slider
      dateSlider.destroy()
    }

    if (!!dateValues.length) {
      slider.ionRangeSlider({
        type: "single",
        skin: "flat",
        values: dateValues,
        prettify: tsToDate,
        grid: true,
        grid_num: 1,
        hide_min_max: true,
        force_edges: true,
        grid_snap: true,
        onFinish: function (selected) {
          onDateChange(map, selected, layerId)
        }
      });
    }

  }

  const getLayerDataset = async (selected_dataset, selected_layer) => {
    if (typeof (datasetsUrl) !== undefined && selected_dataset && selected_layer) {
      if (datasets[selected_dataset]) {
        return datasets[selected_dataset]
      }
      const dataset = await fetch(datasetsUrl + selected_dataset).then(res => res.json())
      datasets[selected_dataset] = dataset
      return dataset
    }
  }

  const updateTileUrl = (tileUrl, params) => {
    // construct new url with new query params
    const url = new URL(tileUrl)
    const qs = new URLSearchParams(url.search);
    Object.keys(params).forEach(key => {
      qs.set(key, params[key])
    })
    url.search = decodeURIComponent(qs);
    return decodeURIComponent(url.href)
  }

  const updateMapLayer = (map, layerConfig, withDate) => {

    const sourceId = layerConfig.source.id
    const layerId = layerConfig.layer.id
    const layerType = layerConfig.layerType

    console.log("layerconfig",layerConfig )

    if (map.getLayer(layerId)) {
      map.removeLayer(layerId)
    }

    if (map.getSource(sourceId)) {
      map.removeSource(sourceId)
    }

    if (withDate) {
      const tileUrl = updateTileUrl(layerConfig.source.tiles, { time: withDate })

      if (layerType === "raster_file" || layerType === "wms") {
        map.addSource(sourceId, {
          type: "raster",
          tiles: [tileUrl],
          tileSize: 256,
        });
        map.addLayer({
          id: layerId,
          type: "raster",
          source: sourceId,
        });
      } else if (layerType === "vector") {
        map.addSource(sourceId, {
          type: "vector",
          tiles: [tileUrl],
        });
        map.addLayer({
          id: layerId,
          type: "fill",
          source: sourceId,
          "source-layer": "default",
          paint: {
            "fill-color": "#088",
            "fill-opacity": 0.6,
          },
        });
      } 

    }


  }

  const getLayerConfig = (layer, tileUrl) => {

    const config = {
      layerType :layer.layerType,
      source: {
        "id": layer.id,
        "type": "raster",
        "tiles": [tileUrl]
      },
      layer: {
        "id": layer.id,
        "type": "raster",
      }
    }

    layerConfigs[layer.id] = config

    return config
  }

  const getLayerDates = async (url) => {
    const res = await fetch(url);
    const res_1 = await res.json();
    return res_1.timestamps;
  }

  const createChoroplethLegend = (legendItems) => {
    // Create the container div and ul elements
    const containerDiv = $('<div>').addClass('c-legend-type-choropleth');
    const ulColors = $('<ul>').attr('id', 'legendColors');
    const ulNames = $('<ul>').attr('id', 'legendNames');

    // Append ul elements to the container div
    containerDiv.append(ulColors, ulNames);


    // Loop through legend items and create elements
    legendItems.forEach(({ color, name }, i) => {
      const colorLi = $('<li>').css('width', `${100 / legendItems.length}%`);
      $('<div>').addClass('icon-choropleth').css('background-color', color).appendTo(colorLi);
      ulColors.append(colorLi);

      const nameLi = $('<li>').css('width', `${100 / legendItems.length}%`);
      $('<span>').addClass('name').text(name).appendTo(nameLi);
      ulNames.append(nameLi);
    });

    return containerDiv
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


  const createLegend = (legendConfig) => {
    const { type, items, ...rest } = legendConfig
    if (type === "choropleth" && items && !!items.length) {

      const thresholds = items.map((item) => item.from || item.name);
      const colors = items.map((item) => item.color);
      return createSvgChoroplethLegend(d3.scaleThreshold(thresholds, colors), {
        tickSize: 0,
        ...rest,
      })
    }
    return null
  }

  const updateLayer = (map, containerId, selected_layer, selected_dataset, layerType) => {
   getLayerDataset(selected_layer, selected_dataset).then(async activeLayerDataset => {

      if (activeLayerDataset) {
        const layer = activeLayerDataset.layers && activeLayerDataset.layers[0]
        console.log(layer)

        const { tileJsonUrl, getCapabilitiesLayerName, getCapabilitiesUrl, paramsSelectorConfig, layerConfig } = layer
        const {currentTimeMethod} = layer

        let layerDates;
        let tileUrl

        
        if (layerType === 'raster'){
          layerDates = await getLayerDates(tileJsonUrl)

          const defaultDate = layerDates && !!layerDates.length && layerDates[0]

          const isoString = new Date(defaultDate).toISOString()
          const res = await fetch(tileJsonUrl);
          const res_1 = await res.json();
          tileUrl = updateTileUrl(res_1.tiles[0], { time: isoString })
          console.log(tileUrl)


        } else if (layerType === 'wms'){
          const timestamps = await getTimeValuesFromWMS(getCapabilitiesUrl, getCapabilitiesLayerName)
          layerDates = timestamps.sort((a, b) => new Date(a) - new Date(b));
          const currentLayerTime = getTimeFromList([...layerDates], currentTimeMethod);
          const timeSelectorConfig = paramsSelectorConfig.find(c => c.key === "time")

          if (timeSelectorConfig) {
            let timeUrlParam = "time"
            const {url_param} = timeSelectorConfig
            if (url_param) {
              timeUrlParam = url_param
            }
            tileUrl = updateTileUrl(layerConfig.source.tiles[0], {[timeUrlParam]: currentLayerTime})
          }
        }

        console.log(layerDates)

        const dateValues = layerDates.map(d => new Date(d).valueOf())
        updateSlider(map, dateValues, layer.id)

        const { legendConfig } = layer || {}

        if (legendConfig) {
          const legend = createLegend(legendConfig)
          $("#legend"+containerId).html(legend)
        }
        
        const layerSetup = getLayerConfig(layer, tileUrl)

        const defaultDate = layerDates && !!layerDates.length && layerDates[0]

        updateMapLayer(map, layerSetup, defaultDate)


      }
    }).catch(e => {
      console.log(e)
    })
  }


  const loadBoundaries = (map) => {
    // fit to country bounds
    if (typeof (countryBounds) !== 'undefined' && countryBounds) {
      const bounds = [[countryBounds[0], countryBounds[1]], [countryBounds[2], countryBounds[3]]]
      map.fitBounds(bounds, { padding: 50 });
    }

    // add country layer
    if (typeof (boundaryTilesUrl) !== 'undefined' && boundaryTilesUrl) {
      // add source
      map.addSource("admin-boundary-source", {
        type: "vector",
        tiles: [boundaryTilesUrl],
      }
      )
      // add layer
      map.addLayer({
        'id': 'admin-boundary-fill',
        'type': 'fill',
        'source': 'admin-boundary-source',
        "source-layer": "default",
        "filter": ["==", "level", 0],
        'paint': {
          'fill-color': "#fff",
          'fill-opacity': 0,
        }
      });

      map.addLayer({
        'id': 'admin-boundary-line',
        'type': 'line',
        'source': 'admin-boundary-source',
        "source-layer": "default",
        "filter": ["==", "level", 0],
        'paint': {
          "line-color": "#C0FF24",
          "line-width": 1,
          "line-offset": 1,
        }
      });
      map.addLayer({
        'id': 'admin-boundary-line-2',
        'type': 'line',
        'source': 'admin-boundary-source',
        "source-layer": "default",
        "filter": ["==", "level", 0],
        'paint': {
          "line-color": "#000",
          "line-width": 1.5,
        }
      });
    }
  }


  initializeMap()


})()