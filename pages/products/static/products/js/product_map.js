const defaultStyle = {
    'version': 8,
    'sources': {
        'carto-dark': {
            'type': 'raster',
            'tiles': [
                "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
                "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
                "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
                "https://d.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"
            ]
        },
        'carto-light': {
            'type': 'raster',
            'tiles': [
                "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
                "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
                "https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
                "https://d.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png"
            ]
        },
        'wikimedia': {
            'type': 'raster',
            'tiles': [
                "https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png"
            ]
        }
    },
    'layers': [{
        'id': 'carto-light-layer',
        'source': 'carto-light',


        'type': 'raster',
        'minzoom': 0,
        'maxzoom': 22
    }]
}


const map = new maplibregl.Map({
    container: "product-map",
    style: defaultStyle,
    doubleClickZoom: false,
});

// Add zoom and rotation controls to the map.
map.addControl(new maplibregl.NavigationControl({showCompass: false}));

map.addControl(new maplibregl.AttributionControl({
    customAttribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    compact: false,
}));

map.addControl(new maplibregl.FullscreenControl());


const slider = $(".layer-date-slider")


const datasets = {}
const layerConfigs = {}

const getActiveLayerDataset = async () => {
    const $activeCategory = $(".map-menu .menu-category.active")
    const activeDataset = $activeCategory.data("dataset")
    const activeLayer = $activeCategory.data("layer")

    if (typeof (datasetsUrl) !== undefined && activeDataset && activeLayer) {
        if (datasets[activeDataset]) {
            return datasets[activeDataset]
        }
        const dataset = await fetch(datasetsUrl + activeDataset).then(res => res.json())
        datasets[activeDataset] = dataset
        return dataset
    }
}

const getLayerConfig = (layer) => {
    const layerConfig = layer.layerConfig
    const tileUrl = layerConfig.source.tiles[0].replace("{geostore_id}", "")

    const config = {
        source: {
            "id": "product-raster-layer",
            "type": "raster",
            "tiles": [tileUrl]
        },
        layer: {
            "id": "product-raster-layer",
            "type": "raster",
        }
    }

    layerConfigs[layer.id] = config

    return config
}

const updateMapLayer = (layerConfig, withDate) => {
    const sourceId = layerConfig.source.id
    const layerId = layerConfig.layer.id

    if (map.getLayer(layerId)) {
        map.removeLayer(layerId)
    }

    if (map.getSource(sourceId)) {
        map.removeSource(sourceId)
    }

    if (withDate) {
        const tileUrl = updateTileUrl(layerConfig.source.tiles, {time: withDate})

        map.addSource(sourceId, {
            type: "raster",
            tiles: [tileUrl]
        });

        map.addLayer({
            id: layerId,
            type: "raster",
            source: sourceId,
        });

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

const getLayerDates = (url) => {
    return fetch(url).then(res => res.json()).then(res => res.timestamps)
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

const onDateChange = (selectedDate, layerId) => {
    const {from_value} = selectedDate
    const isoString = new Date(from_value).toISOString()

    const layerConfig = layerConfigs[layerId]

    if (layerConfig) {
        updateSourceTileUrl(map, layerConfig.source.id, {time: isoString})
    }
}


const updateSlider = (dateValues, layerId) => {
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
                onDateChange(selected, layerId)
            }
        });
    }

}

const createChoroplethLegend = (legendItems) => {
    // Create the container div and ul elements
    const containerDiv = $('<div>').addClass('c-legend-type-choropleth');
    const ulColors = $('<ul>').attr('id', 'legendColors');
    const ulNames = $('<ul>').attr('id', 'legendNames');

    // Append ul elements to the container div
    containerDiv.append(ulColors, ulNames);


    // Loop through legend items and create elements
    legendItems.forEach(({color, name}, i) => {
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
    const {type, items, ...rest} = legendConfig
    if (type === "choropleth" && items && !!items.length) {
        const thresholds = items.map((item) => item.value || item.name);
        const colors = items.map((item) => item.color);
        return createSvgChoroplethLegend(d3.scaleThreshold(thresholds, colors), {
            tickSize: 0,
            ...rest,
        })
    }
    return null
}

const updateLegend = (layer) => {

    const {legendConfig} = layer || {}

    if (legendConfig) {
        const legend = createLegend(legendConfig)
        $("#legendContainer").html(legend)
    }

}


const updateLayer = () => {
    getActiveLayerDataset().then(activeLayerDataset => {

        if (activeLayerDataset) {
            const layer = activeLayerDataset.layers && activeLayerDataset.layers[0]

            const {tileJsonUrl} = layer

            if (tileJsonUrl) {
                getLayerDates(tileJsonUrl).then(layerDates => {

                    const layerConfig = getLayerConfig(layer)

                    const defaultDate = layerDates && !!layerDates.length && layerDates[0]

                    updateMapLayer(layerConfig, defaultDate)

                    const dateValues = layerDates.map(d => new Date(d).valueOf())
                    updateSlider(dateValues, layer.id)


                    updateLegend(layer)
                })
            }
        }
    }).catch(e => {
        console.log(e)
    })
}

const $layerInput = $(".menu-category")

$layerInput.on("click", function (e) {
    const $this = $(this)
    const $layer = $this.find(".layer-title")
    const selectedLayerId = $layer.data("layer")

    if (selectedLayerId) {
        $layerInput.removeClass("active")

        $this.addClass("active")
        updateLayer()
    }
})

map.on("load", () => {
    // fit to country bounds
    if (typeof (countryBounds) !== 'undefined' && countryBounds) {
        const bounds = [[countryBounds[0], countryBounds[1]], [countryBounds[2], countryBounds[3]]]
        map.fitBounds(bounds, {padding: 50});
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


    updateLayer()
})



