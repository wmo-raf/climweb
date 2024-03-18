$(document).ready(function () {

    let forecastSettings;

    // default MapLibre style
    const defaultStyle = {
        'version': 8,
        "glyphs": "https://tiles.basemaps.cartocdn.com/fonts/{fontstack}/{range}.pbf",
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
            'voyager': {
                'type': 'raster',
                'tiles': [
                    "https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png",
                    "https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png",
                    "https://c.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png",
                    "https://d.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png",

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
        container: "home-map", // container ID
        style: defaultStyle,
        center: [0, 0], // starting position [lng, lat]
        zoom: 4, // starting zoom
        scrollZoom: false,
    });

    // Create a popup object
    const popup = new maplibregl.Popup({
        closeButton: false,
        closeOnClick: false
    });


    // Add zoom and rotation controls to the map.
    map.addControl(new maplibregl.NavigationControl({showCompass: false}));

    map.addControl(new maplibregl.AttributionControl({
        customAttribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
        compact: false,

    }));

    const getPopupHTML = (props) => {
        const dataParams = forecastSettings?.parameters || []
        if (dataParams && dataParams.length === 0) {
            return null
        }

        const paramValues = dataParams.reduce((all, param) => {
            if (props[param.parameter]) {
                all[param.name] = `${props[param.parameter]} ${param.parameter_unit}`
            }
            return all
        }, {})

        const cityName = props.city;
        const citySlug = props.city_slug;
        const condition = props.condition_label;

        let values = Object.keys(paramValues).reduce((all, key) => {
            all = all + `<p class="py-0" style="padding:0.5em 0"><b>${key}: </b>${paramValues[key]}</p>`
            return all
        }, "")

        let detailLink
        if (cityDetailUrl) {
            const detailUrl = cityDetailUrl + citySlug
            detailLink = `<a class="button is-small is-light mt-2" target="_blank" rel="noopender noreferrer" href="${detailUrl}"> 
                            <span>Details</span>
                            <span class="icon">
                                <i class="fa-solid fa-arrow-trend-up"></i>
                            </span> 
                        </a>`
        }


        return `<div class="block" style="margin:10px; width:200px">
            <h2 class="title" style="font-size:18px;">${cityName}</h2>
            <h2 class="subtitle mb-0" style="font-size:14px;">${condition}</h2>
            ${detailLink ? detailLink : ""}
            <hr>
            ${values}

            
        </div>`
    }

    map.on("load", () => {
        if (weatherIconsUrl) {
            fetch(weatherIconsUrl).then(response => response.json()).then(icons => {
                icons.forEach(icon => {
                    map.loadImage(icon.url).then(image => {
                        map.addImage(icon.id, image.data);
                    });
                });
            });
        }

        if (forecastSettingsUrl) {
            fetch(forecastSettingsUrl).then(response => response.json()).then(settings => {
                forecastSettings = settings
            });
        }


        // fit to country bounds
        if (countryBounds) {
            const bounds = [[countryBounds[0], countryBounds[1]], [countryBounds[2], countryBounds[3]]]
            map.fitBounds(bounds, {padding: 50});
        } else {
            if (country_info && country_info.bbox) {

                const bbox = country_info.bbox

                map.fitBounds(bbox, {padding: 50});
            }
        }

        // add country layer
        if (boundaryTilesUrl) {
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

        // add cap alerts layer
        if (alertsGeojson) {
            map.addSource("alert-areas", {
                type: "geojson",
                data: alertsGeojson,
            });

            map.addLayer({
                id: "alert-areas-layer",
                type: "fill",
                source: "alert-areas",
                paint: {
                    "fill-color": [
                        "case",
                        ["==", ["get", "severity"], "Extreme"],
                        "#d72f2a",
                        ["==", ["get", "severity"], "Severe"],
                        "#f89904",
                        ["==", ["get", "severity"], "Moderate"],
                        "#e4e616",
                        ["==", ["get", "severity"], "Minor"],
                        "#53ffff",
                        ["==", ["get", "severity"], "Unknown"],
                        "#3366ff",
                        "black",
                    ],
                    "fill-opacity": 0.7,
                    "fill-outline-color": "#000",
                },
            });

            // CAP alerts layer on click
            map.on("click", "alert-areas-layer", (e) => {
                // Copy coordinates array.

                const description = e.features[0].properties.areaDesc;
                const severity = e.features[0].properties.severity;
                const event = e.features[0].properties.event;

                new maplibregl.Popup()
                    .setLngLat(e.lngLat)
                    .setHTML(`<div class="block" style="margin:10px"><h2 class="title" style="font-size:15px;">${description}</h2> <h2 class="subtitle" style="font-size:14px;">${event}</h2> <hr> <p>${severity} severity</p> </a></div>`)
                    .addTo(map);


            });

            // Change the cursor to a pointer when the mouse is over the alerts layer.
            map.on("mouseenter", "alert-areas-layer", () => {
                map.getCanvas().style.cursor = "pointer";
            });

            // Change it back to a pointer when it leaves.
            map.on("mouseleave", "alert-areas-layer", () => {
                map.getCanvas().style.cursor = "";
            });
        }

        // add city forecast source
        map.addSource("city-forecasts", {
            type: "geojson",
            cluster: true,
            clusterMinPoints: 2,
            clusterRadius: 25,
            data: {type: "FeatureCollection", features: []}
        })

        // add city forecast layer
        map.addLayer({
            "id": "city-forecasts",
            "type": "symbol",
            "layout": {
                'icon-image': ['get', 'condition'],
                'icon-size': 0.3,
                'icon-allow-overlap': true
            },
            source: "city-forecasts"
        })

        // city forecast on click
        map.on("click", "city-forecasts", (e) => {
            // Get the feature that was hovered over
            const coordinates = e.features[0].geometry.coordinates.slice()
            const feature = e.features[0];
            map.getCanvas().style.cursor = "pointer";

            // Ensure that if the map is zoomed out such that multiple
            // copies of the feature are visible, the popup appears
            // over the copy being pointed to.
            while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
                coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
            }

            const popupHTML = getPopupHTML(feature.properties)

            if (popupHTML) {
                new maplibregl.Popup().setLngLat(e.lngLat)
                    .setHTML(popupHTML)
                    .addTo(map);
            }


        });

        // Change it back to a pointer when it leaves.
        map.on("mouseleave", "city-forecasts", () => {
            map.getCanvas().style.cursor = "";
        });

        const initDate = document.getElementById("daily_forecast");
        if (initDate && initDate.value) {
            setForecastData({forecast_date: initDate.value})
        }
    })


    function setForecastData(params) {
        const {forecast_date} = params
        fetch(forecast_api).then(res => res.json()).then(data => {
            const selectedDateData = data.find(d => d.date === forecast_date)
            if (selectedDateData) {
                map.getSource("city-forecasts").setData(selectedDateData)
            }
        })
    }

    // toggle forecasts by selected date
    $('#daily_forecast').on('change', function (e) {
        setForecastData({forecast_date: e.target.value})
    });

});