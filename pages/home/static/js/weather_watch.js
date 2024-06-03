$((async function () {
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
                },
            },
            'layers': [{
                'id': 'carto-light-layer',
                'source': 'carto-light',
                'type': 'raster',
                'minzoom': 0,
                'maxzoom': 22
            }]
        }

        const {
            zoomLocations,
            bounds,
            boundaryTilesUrl,
            weatherIconsUrl,
            forecastSettingsUrl,
            countryInfo,
            homeMapAlertsUrl,
            forecastDataApiUrl,
            capGeojsonUrl,
        } = await fetch(homeMapSettingsUrl).then(response => response.json())


        // create map
        const map = new maplibregl.Map({
            container: "home-map", // container ID
            style: defaultStyle,
            center: [0, 0],
            zoom: 4,
            scrollZoom: false,
        });

        const basemaps = {
            'carto-light': 'carto-light-layer',
            'carto-dark': 'carto-dark-layer',
            'voyager': 'voyager-layer',
            'wikimedia': 'wikimedia-layer'
        };

        Object.keys(basemaps).forEach(basemap => {

            document.getElementById(basemap).addEventListener('click', () => {
                setBasemap(map,basemap);
            });
        })
        
        function setBasemap(map,style) {
            Object.keys(basemaps).forEach(layer => {
                if (map.getLayer(basemaps[layer])) {
                    map.removeLayer(basemaps[layer]);
                    map.removeSource(layer);
                }
            });
        
            if(map.getSource(style)){
                map.removeSource(style)
            }

            if(map.getLayer(basemaps[style])){
                map.removeLayer(basemaps[style])
            }
            map.addSource(style, defaultStyle.sources[style]);
        
            map.addLayer({
                'id': basemaps[style],
                'source': style,
                'type': 'raster',
                'minzoom': 0,
                'maxzoom': 22
            },map.getStyle().layers[0].id);
        }


        // Add zoom control to the map.
        map.addControl(new maplibregl.NavigationControl({showCompass: false}));

        // add fullscreen control
        map.addControl(new maplibregl.FullscreenControl());

        // add attribution
        map.addControl(new maplibregl.AttributionControl({
            customAttribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
            compact: false,
        }));

        // fetch all weather icons and load to map
        if (weatherIconsUrl) {
            fetch(weatherIconsUrl).then(response => response.json()).then(icons => {
                icons.forEach(icon => {
                    map.loadImage(icon.url).then(image => {
                        map.addImage(icon.id, image.data);
                    });
                });
            });
        }

        // fetch forecast settings
        if (forecastSettingsUrl) {
            fetch(forecastSettingsUrl).then(response => response.json()).then(settings => {
                forecastSettings = settings
            });
        }

        // wait for map to load
        await new Promise((resolve) => map.on("load", resolve));

        // add boundary layer
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

        
        let zoomLocationsInit = false
        const updateMapBounds = () => {
            if (bounds) {
                const mapBounds = [[bounds[0], bounds[1]], [bounds[2], bounds[3]]]
                map.fitBounds(mapBounds, {padding: 50});
            } else {
                if (countryInfo && countryInfo.bbox) {
                    const bbox = countryInfo.bbox
                    map.fitBounds(bbox, {padding: 50});
                }
            }

            if (!zoomLocationsInit) {
                initZoomLocations()
                zoomLocationsInit = true
            }
        }

        const initZoomLocations = () => {
            // Zoom Locations
            if (zoomLocations && !!zoomLocations.length) {
                map.addControl(new ZoomToLocationsControl(zoomLocations), 'top-right');
            }

            const defaultZoomLocation = zoomLocations.find(loc => loc.default)

            if (defaultZoomLocation && defaultZoomLocation.bounds) {
                map.fitBounds(defaultZoomLocation.bounds, {
                    padding: 50
                });
            }
        }

        if (homeMapAlertsUrl) {
            // CAP Alerts
            fetch(homeMapAlertsUrl)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Error fetching alerts');
                    }
                    return response.text();
                })
                .then(alertsHTML => {
                    const $alerts = $(alertsHTML)

                    if ($alerts.length) {
                        $alerts.appendTo("#alerts-container")
                        $("#alerts-legend").show()
                        fetch(capGeojsonUrl).then(response => response.json()).then(geojsonAlertsData => {
                            if (geojsonAlertsData.features.length > 0) {
                                const bounds = turf.bbox(geojsonAlertsData);

                                // fit map to alert bounds
                                map.fitBounds(bounds, {padding: 50});

                                // add cap alerts layer
                                map.addSource("alert-areas", {
                                    type: "geojson",
                                    data: geojsonAlertsData,
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
                                }, "city-forecasts");

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
                            } else {
                                updateMapBounds()
                            }
                        }).catch(error => {
                            console.error("HOME_MAP_ALERTS_GEOJSON_ERROR:", error)
                            updateMapBounds()
                        })
                    }
                })
                .catch(error => {
                    console.error("HOME_MAP_ALERTS_ERROR:", error)
                    updateMapBounds()
                })
        } else {
            updateMapBounds()
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

        const getForecastData = async () => {
            return fetch(forecastDataApiUrl).then(res => res.json())
        }
        const forecastData = await getForecastData()

        const dates = forecastData.map(d => d.date)
        const dateSelector = $("#forecast-dates")

        dates.forEach((date, i) => {
            const option = document.createElement("option")
            option.value = date
            option.text = new Date(date).toDateString()
            if (i === 0) {
                option.selected = true
            }
            dateSelector.append(option)
        })

        if (!!dates.length) {
            dateSelector.show()
        }


        const setForecastData = (date) => {
            const selectedDateData = forecastData.find(d => d.date === date)
            if (selectedDateData) {
                map.getSource("city-forecasts").setData(selectedDateData)
            }
        }

        // Get the latest date
        const latestDate = dateSelector.val()
        setForecastData(latestDate)

        dateSelector.on("change", (e) => {
            setForecastData(e.target.value)
        })


    }
));