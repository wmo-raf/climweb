const defaultStyle = {
    'version': 8, "glyphs": "https://tiles.basemaps.cartocdn.com/fonts/{fontstack}/{range}.pbf", 'sources': {
        'carto-dark': {
            'type': 'raster',
            'tiles': ["https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png", "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png", "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png", "https://d.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"]
        }, 'carto-light': {
            'type': 'raster',
            'tiles': ["https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png", "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png", "https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png", "https://d.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png"]
        }, 'voyager': {
            'type': 'raster',
            'tiles': ["https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png", "https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png", "https://c.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png", "https://d.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png",

            ]
        }, 'wikimedia': {
            'type': 'raster', 'tiles': ["https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png"]
        },
    }, 'layers': [{
        'id': 'carto-light-layer', 'source': 'carto-light', 'type': 'raster', 'minzoom': 0, 'maxzoom': 22, "layout": {
            "visibility": "visible"
        }, "metadata": {
            "mapbox:groups": "background"
        }
    }, {
        'id': 'carto-dark-layer', 'source': 'carto-dark', 'type': 'raster', 'minzoom': 0, 'maxzoom': 22, "layout": {
            "visibility": "none"
        }, "metadata": {
            "mapbox:groups": "background"
        }
    }, {
        'id': 'voyager-layer', 'source': 'voyager', 'type': 'raster', 'minzoom': 0, 'maxzoom': 22, "layout": {
            "visibility": "none"
        }, "metadata": {
            "mapbox:groups": "background"
        }
    }, {
        'id': 'wikimedia-layer', 'source': 'wikimedia', 'type': 'raster', 'minzoom': 0, 'maxzoom': 22, "layout": {
            "visibility": "none"
        }, "metadata": {
            "mapbox:groups": "background"
        }
    },]
}

class WeatherWatch {
    constructor(mapContainer, options) {
        this.mapContainer = mapContainer
        this.options = options

        this.map = null
        this.forecastSettings = null

        this.basemaps = {
            "carto-light": {
                name: 'Carto Light', layer: "carto-light-layer",
            }, "carto-dark": {
                name: 'Carto Dark', layer: "carto-dark-layer",
            }, "voyager": {
                name: 'Voyager', layer: "voyager-layer",
            }, "wikimedia": {
                name: 'Wikimedia', layer: "wikimedia-layer",
            }
        }

        this.initMap()
    }

    initMap() {
        const initialBounds = this.options.initialBounds || null

        // create map
        this.map = new maplibregl.Map({
            container: this.mapContainer, style: defaultStyle, center: [0, 0], zoom: 4, scrollZoom: false,
        });

        // fit map to initial country bounds
        if (initialBounds) {
            const mapBounds = [[initialBounds[0], initialBounds[1]], [initialBounds[2], initialBounds[3]]]
            this.map.fitBounds(mapBounds, {padding: 50});
        }

        // Add zoom control to the map.
        this.map.addControl(new maplibregl.NavigationControl({showCompass: false}));

        // add fullscreen control
        this.map.addControl(new maplibregl.FullscreenControl());

        // add attribution
        this.map.addControl(new maplibregl.AttributionControl({
            customAttribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
            compact: false,
        }));

        // initialize basemap selector
        this.initBasemapSelector()

        this.map.on("load", () => {
            this.fetchSettings().then((settings) => {
                const {
                    zoomLocations,
                    boundaryTilesUrl,
                    weatherIconsUrl,
                    forecastSettingsUrl,
                    homeMapAlertsUrl,
                    homeForecastDataUrl,
                    capGeojsonUrl,
                } = settings


                // add country boundary layer
                this.addBoundaryLayer(boundaryTilesUrl)

                // add warnings layer
                this.addWarningsLayer(homeMapAlertsUrl, capGeojsonUrl)

                // initialize city forecast
                this.initCityForecast(homeForecastDataUrl, weatherIconsUrl)

                // initialize zoom locations. Allow to zoom in to custom locations
                // useful for islands or disputed territories
                this.initZoomLocations(zoomLocations)


                this.getCityForecastSettings(forecastSettingsUrl)

            })
        })
    }

    initBasemapSelector() {
        Object.keys(this.basemaps).forEach(basemap => {
            const basemapEl = document.getElementById(basemap)
            if (basemapEl) {
                basemapEl.addEventListener('click', () => {
                    this.changeBasemap(basemap)
                });
            }
        })
    }

    changeBasemap(layerId) {
        const mapStyle = this.map.getStyle()
        const backgroundLayers = mapStyle.layers.filter(layer => layer.metadata && layer.metadata["mapbox:groups"] === "background")

        backgroundLayers.forEach(layer => {
            if (layer.id === this.basemaps[layerId].layer) {
                this.map.setLayoutProperty(layer.id, 'visibility', 'visible')
            } else {
                this.map.setLayoutProperty(layer.id, 'visibility', 'none')
            }
        })
    }

    fetchSettings() {
        const {mapSettingsUrl} = this.options
        return fetch(mapSettingsUrl).then(response => response.json())
    }

    getCityForecastSettings(forecastSettingsUrl) {
        fetch(forecastSettingsUrl).then(response => response.json()).then(settings => {
            this.forecastSettings = settings
        });
    }

    getWeatherIcons(weatherIconsUrl) {
        fetch(weatherIconsUrl).then(response => response.json()).then(icons => {
            icons.forEach(icon => {
                this.map.loadImage(icon.url).then(image => {
                    this.map.addImage(icon.id, image.data);
                });
            });
        });
    }

    addBoundaryLayer(boundaryTilesUrl) {
        // add source
        this.map.addSource("admin-boundary-source", {
            type: "vector", tiles: [boundaryTilesUrl],
        })
        // add layer
        this.map.addLayer({
            'id': 'admin-boundary-fill',
            'type': 'fill',
            'source': 'admin-boundary-source',
            "source-layer": "default",
            "filter": ["==", "level", 0],
            'paint': {
                'fill-color': "#fff", 'fill-opacity': 0,
            }
        });

        this.map.addLayer({
            'id': 'admin-boundary-line',
            'type': 'line',
            'source': 'admin-boundary-source',
            "source-layer": "default",
            "filter": ["==", "level", 0],
            'paint': {
                "line-color": "#C0FF24", "line-width": 1, "line-offset": 1,
            }
        });
        this.map.addLayer({
            'id': 'admin-boundary-line-2',
            'type': 'line',
            'source': 'admin-boundary-source',
            "source-layer": "default",
            "filter": ["==", "level", 0],
            'paint': {
                "line-color": "#000", "line-width": 1.5,
            }
        });

    }

    addWarningsLayer(homeMapAlertsUrl, capGeojsonUrl) {
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
                    const wrapper = $alerts[0]

                    // Show alerts legend only if alerts are available
                    if (wrapper.dataset.alertsAvailable === "true") {
                        $("#alerts-legend").show()
                    }

                    fetch(capGeojsonUrl).then(response => response.json()).then(geojsonAlertsData => {
                        if (geojsonAlertsData.features.length > 0) {
                            const bounds = turf.bbox(geojsonAlertsData);

                            // fit map to alert bounds
                            this.map.fitBounds(bounds, {padding: 50});

                            // add cap alerts layer
                            this.map.addSource("alert-areas", {
                                type: "geojson", data: geojsonAlertsData,
                            });

                            this.map.addLayer({
                                id: "alert-areas-layer", type: "fill", source: "alert-areas", paint: {
                                    "fill-color": ["case", ["==", ["get", "severity"], "Extreme"], "#d72f2a", ["==", ["get", "severity"], "Severe"], "#f89904", ["==", ["get", "severity"], "Moderate"], "#e4e616", ["==", ["get", "severity"], "Minor"], "#53ffff", ["==", ["get", "severity"], "Unknown"], "#3366ff", "black",],
                                    "fill-opacity": 0.7,
                                    "fill-outline-color": "#000",
                                },
                            }, "city-forecasts");

                            // CAP alerts layer on click
                            this.map.on("click", "alert-areas-layer", (e) => {
                                // Copy coordinates array.
                                const description = e.features[0].properties.areaDesc;
                                const severity = e.features[0].properties.severity;
                                const event = e.features[0].properties.event;

                                new maplibregl.Popup()
                                    .setLngLat(e.lngLat)
                                    .setHTML(`<div class="block" style="margin:10px"><h2 class="title" style="font-size:15px;">${description}</h2> <h2 class="subtitle" style="font-size:14px;">${event}</h2> <hr> <p>${severity} severity</p> </a></div>`)
                                    .addTo(this.map);
                            });

                            // Change the cursor to a pointer when the mouse is over the alerts layer.
                            this.map.on("mouseenter", "alert-areas-layer", () => {
                                this.map.getCanvas().style.cursor = "pointer";
                            });

                            // Change it back to a pointer when it leaves.
                            this.map.on("mouseleave", "alert-areas-layer", () => {
                                this.map.getCanvas().style.cursor = "";
                            });
                        }
                    }).catch(error => {
                        console.error("HOME_MAP_ALERTS_GEOJSON_ERROR:", error)
                    })
                }
            })
            .catch(error => {
                console.error("HOME_MAP_ALERTS_ERROR:", error)
            })
    }

    initZoomLocations(zoomLocations) {
        // Add zoom locations control
        if (zoomLocations && !!zoomLocations.length) {
            this.map.addControl(new ZoomToLocationsControl(zoomLocations), 'bottom-right');
        }

        // get default zoom location if any
        const defaultZoomLocation = zoomLocations.find(loc => loc.default)

        // fit map to default zoom location bounds
        if (defaultZoomLocation && defaultZoomLocation.bounds) {
            this.map.fitBounds(defaultZoomLocation.bounds, {
                padding: 50
            });
        }
    }

    initCityForecast(homeForecastDataUrl, weatherIconsUrl) {
        // add city forecast source
        this.map.addSource("city-forecasts", {
            type: "geojson",
            cluster: true,
            clusterMinPoints: 2,
            clusterRadius: 25,
            data: {type: "FeatureCollection", features: []}
        })

        // add city forecast layer
        this.map.addLayer({
            "id": "city-forecasts", "type": "symbol", "layout": {
                'icon-image': ['get', 'condition'], 'icon-size': 0.3, 'icon-allow-overlap': true
            }, source: "city-forecasts"
        })

        // setup city forecast interactions
        this.setupCityForecastInteractions()

        // fetch city forecast data
        fetch(homeForecastDataUrl).then(res => res.json()).then(data => {
            // get and set weather icons
            this.getWeatherIcons(weatherIconsUrl)

            // set city forecast data
            this.setCityForecastData(data)
        })
    }

    setCityForecastData(data) {
        const {multi_period: isMultiPeriod, data: forecastData} = data

        this.forecastData = forecastData

        const dates = this.forecastData.map(d => d.datetime)

        this.cityForecastDateSelector = $("#forecast-dates")

        dates.forEach((date, i) => {
            const dObj = new Date(date)
            const now = new Date()

            if (isMultiPeriod && dObj.toDateString() === now.toDateString() && dObj.getHours() < now.getHours()) {
                return
            }

            const option = document.createElement("option")
            option.value = date


            if (isMultiPeriod) {
                option.text = dObj.toDateString() + " - " + dObj.getHours() + ":00"
            } else {
                option.text = dObj.toDateString()
            }

            if (i === 0) {
                option.selected = true
            }
            this.cityForecastDateSelector.append(option)
        })

        if (!!dates.length) {
            this.cityForecastDateSelector.show()
        }

        this.cityForecastDateSelector.on("change", (e) => {
            this.updateMapCityForecastData(e.target.value)
        })

        // Get the latest date
        const latestDate = this.cityForecastDateSelector.val()
        this.updateMapCityForecastData(latestDate)
    }

    updateMapCityForecastData(date) {
        const selectedDateData = this.forecastData.find(d => d.datetime === date)
        if (selectedDateData) {
            this.map.getSource("city-forecasts").setData(selectedDateData)
        }
    }

    setupCityForecastInteractions() {
        // city forecast on click
        this.map.on("click", "city-forecasts", (e) => {
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

            const popupHTML = this.getCityForecastPopupHTML(feature.properties)

            if (popupHTML) {
                new maplibregl.Popup().setLngLat(e.lngLat)
                    .setHTML(popupHTML)
                    .addTo(this.map);
            }
        });

        // Change it back to a pointer when it leaves.
        this.map.on("mouseleave", "city-forecasts", () => {
            this.map.getCanvas().style.cursor = "";
        });
    }

    getCityForecastPopupHTML(props) {
        const dataParams = this.forecastSettings?.parameters || []

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
}