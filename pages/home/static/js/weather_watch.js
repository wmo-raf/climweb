$(document).ready(function () {
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


    const forecast_map = new maplibregl.Map({
        container: "home-map", // container ID
        style: defaultStyle,
        center: [30.019531249998607, 16.130262012034265], // starting position [lng, lat]
        zoom: 4.2, // starting zoom
        scrollZoom: false,
    });

    // Create a popup object
    var popup = new maplibregl.Popup({
        closeButton: false,
        closeOnClick: false
    });


    // Add zoom and rotation controls to the map.
    forecast_map.addControl(new maplibregl.NavigationControl({showCompass: false}));

    forecast_map.addControl(new maplibregl.AttributionControl({
        customAttribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
        compact: false,

    }));

    const allAreas = $(".alert-area")
        .map(function () {

            return this.value;
        })
        .get();

    const getPopupHTML = (props) => {
        const paramValues = dataParams.reduce((all, param) => {
            if (props[param.parameter]) {
                all[param.name] = props[param.parameter]
            }
            return all
        }, {})

        const cityName = props.city_name;
        const condition = props.condition;

        let values = Object.keys(paramValues).reduce((all, key) => {
            all = all + `<p><b>${key}: </b>${paramValues[key]}</p>`
            return all
        }, "")

        return `<div class="block" style="margin:10px; width:200px">
            <h2 class="title" style="font-size:18px;">${cityName}</h2>
            <h2 class="subtitle" style="font-size:14px;">${condition}</h2>
            <hr>
            ${values}
        </div>`
    }

    function populateMap(data) {
        forecast_map.addSource("city-forecasts", {
            type: "geojson",
            data: data
        })

        forecast_map.addLayer({
            "id": "city-forecasts",
            "type": "symbol",
            "layout": {
                'icon-image': ['get', 'condition_icon'],
                'icon-size': 0.3,
                'icon-allow-overlap': true
            },
            source: "city-forecasts"
        })

        // forecast_map.addLayer({
        //     id: "city-forecasts-max_temp",
        //     source: "city-forecasts",
        //     type: "symbol",
        //     'layout': {
        //         'text-offset': [2, -0.5],
        //         'text-field': ['concat', ['get', 'air_temperature_max'], temp_units],
        //         'text-allow-overlap': true,
        //         'icon-allow-overlap': true

        //     },
        //     'paint': {
        //         'text-halo-color': '#fff',
        //         'text-halo-width': 2,


        //     }

        // })
        // forecast_map.addLayer({
        //     id: "city-forecasts-min_temp",
        //     source: "city-forecasts",
        //     type: "symbol",
        //     'layout': {
        //         'text-offset': [2.5, 0.5],
        //         'text-field': ['concat', ['get', 'air_temperature_min'], temp_units],
        //         'text-size': 12,
        //         'text-allow-overlap': true,
        //         'icon-allow-overlap': true


        //     },
        //     'paint': {
        //         'text-halo-color': '#fff',
        //         'text-halo-width': 2,

        //     }

        // })


    }

    forecast_map.on("load", () => {

        if (country_info && country_info.bbox) {

            const bbox = country_info.bbox

            forecast_map.fitBounds(bbox, {padding: 20});
        }

        if (alertsGeojson) {
            forecast_map.addSource("alert-areas", {
                type: "geojson",
                data: alertsGeojson,
            });

            forecast_map.addLayer({
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

            // When a click event occurs on a feature in the places layer, open a popup at the
            // location of the feature, with description HTML from its properties.
            forecast_map.on("click", "alert-areas-layer", (e) => {
                // Copy coordinates array.

                const description = e.features[0].properties.areaDesc;
                const severity = e.features[0].properties.severity;
                const event = e.features[0].properties.event;

                new maplibregl.Popup()
                    .setLngLat(e.lngLat)
                    .setHTML(`<div class="block" style="margin:10px"><h2 class="title" style="font-size:15px;">${description}</h2> <h2 class="subtitle" style="font-size:14px;">${event}</h2> <hr> <p>${severity} severity</p></div>`)
                    .addTo(forecast_map);
            });

            // Change the cursor to a pointer when the mouse is over the places layer.
            forecast_map.on("mouseenter", "alert-areas-layer", () => {
                forecast_map.getCanvas().style.cursor = "pointer";
            });

            // Change it back to a pointer when it leaves.
            forecast_map.on("mouseleave", "alert-areas-layer", () => {
                forecast_map.getCanvas().style.cursor = "";
            });
        }


        // When a click event occurs on a feature in the places layer, open a popup at the
        // location of the feature, with description HTML from its properties.
        forecast_map.on("mouseenter", "city-forecasts", (e) => {
            // Get the feature that was hovered over
            var feature = e.features[0];
            forecast_map.getCanvas().style.cursor = "pointer";

            // Copy coordinates array.
            const city_name = feature.properties.city_name;
            const condition_desc = feature.properties.condition;
            const min_temp = feature.properties.min_temp;
            const max_temp = feature.properties.max_temp;


            popup.setLngLat(feature.geometry.coordinates)
                .setHTML(getPopupHTML(feature.properties))
                .addTo(forecast_map);
        })
        //  i am here    

        // Change it back to a pointer when it leaves.
        forecast_map.on("mouseleave", "city-forecasts", () => {
            popup.remove()
            forecast_map.getCanvas().style.cursor = "";
        });

        var initDate = document.getElementById("daily_forecast");
        setForecastData(initDate.value)


    })

    function setForecastData(forecast_date) {
        // Make an HTTP GET request to the API endpoint
        fetch(`${forecast_api}?forecast_date=${forecast_date}`)
            .then(response => response.json())  // Parse the response as JSON
            .then(data => {
                // Process the retrieved data
                data.map(icon => {


                    let img = new Image()

                    img.onload = () => {
                        if (!forecast_map.hasImage(icon.properties.condition_icon)) {
                            return forecast_map.addImage(`${icon.properties.condition_icon}`, img)
                        }

                    }
                    img.src = `${static_path}${icon.properties.condition_icon}`
                    return img.src

                })
                // Access and use the data as needed                
                populateMap({
                    type: "FeatureCollection",
                    features: data
                })


            })
            .catch(error => {
                // Handle any errors that occurred during the request
                console.error('Error:', error);
            });

    }


    // toggle forecasts by selected date
    $('#daily_forecast').on('change', function (e) {
        var valueSelected = this.value;

        if (forecast_map.getLayer("city-forecasts")) {
            forecast_map.removeLayer("city-forecasts");
        }
        if (forecast_map.getLayer("city-forecasts-max_temp")) {
            forecast_map.removeLayer("city-forecasts-max_temp");
        }

        if (forecast_map.getLayer("city-forecasts-min_temp")) {
            forecast_map.removeLayer("city-forecasts-min_temp");
        }
        if (forecast_map.getSource("city-forecasts")) {
            forecast_map.removeSource("city-forecasts");
        }

        setForecastData(valueSelected)

    });
    // }

});