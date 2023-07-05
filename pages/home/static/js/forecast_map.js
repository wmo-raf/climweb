$(document).ready(function () {
    // code to be executed when the DOM is ready

    const forecast_map = new maplibregl.Map({
        container: "home-map", // container ID
        style: basemap,
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
    forecast_map.addControl(new maplibregl.NavigationControl());

    const allAreas = $(".alert-area")
        .map(function () {
            return JSON.parse(this.value);
        })
        .get();

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

        forecast_map.addLayer({
            id: "city-forecasts-max_temp",
            source: "city-forecasts",
            type: "symbol",
            'layout': {
                'text-offset': [2, -0.5],
                'text-field': ['concat', ['get', 'max_temp'], temp_units],
                'text-allow-overlap': true,
                'icon-allow-overlap': true

            },
            'paint': {
                'text-halo-color': '#fff',
                'text-halo-width': 2,


            }

        })
        forecast_map.addLayer({
            id: "city-forecasts-min_temp",
            source: "city-forecasts",
            type: "symbol",
            'layout': {
                'text-offset': [2.5, 0.5],
                'text-field': ['concat', ['get', 'min_temp'], temp_units],
                'text-size': 12,
                'text-allow-overlap': true,
                'icon-allow-overlap': true


            },
            'paint': {
                'text-halo-color': '#fff',
                'text-halo-width': 2,

            }

        })


    }

    function setForecastData(forecast_date) {

        // Make an HTTP GET request to the API endpoint
        fetch(`${BASE_PATH}api/forecasts?forecast_date=${forecast_date}`)
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
                    img.src = `${BASE_PATH}${icon.properties.condition_icon}`
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

    var initDate = document.getElementById("daily_forecast");
    setForecastData(initDate.value)



    forecast_map.on("load", () => {

        if (country_info && country_info.bbox) {

            const bbox = country_info.bbox

            forecast_map.fitBounds(bbox, { padding: 20 });
        }

        if (allAreas.length > 0) {
            var polyFeature = [];
            allAreas.map((area) => {
                // Remove the SRID prefix
                const wktWithoutSrid = area.area.replace(/^SRID=\d+;/, "");

                // Extract the coordinates from the polygon string using a regex pattern
                const match = /\((.*?)\)/.exec(wktWithoutSrid);

                revCoords = [];

                if (match) {
                    const coordinatePairs = match[1].split(", ");
                    const coordinates = coordinatePairs.map((pair) =>
                        pair.replace("(", "").split(" ").map(parseFloat)
                    );

                    polyFeature.push({
                        type: "Feature",
                        geometry: {
                            type: "Polygon",
                            coordinates: [coordinates],
                        },
                        properties: {
                            areaDesc: area.areaDesc,
                            severity: area.severity,
                            severityInfo: area.severityInfo,
                            event: area.event
                        },
                    });
                }
            });

            forecast_map.addSource("alert-areas", {
                type: "geojson",
                data: {
                    type: "FeatureCollection",
                    features: polyFeature,
                },
            });

            forecast_map.addLayer({
                id: "alert-areas-layer",
                type: "fill",
                source: "alert-areas",
                paint: {
                    "fill-color": "#088",
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
                },
            });

            // When a click event occurs on a feature in the places layer, open a popup at the
            // location of the feature, with description HTML from its properties.
            forecast_map.on("click", "alert-areas-layer", (e) => {
                // Copy coordinates array.
                const description = e.features[0].properties.areaDesc;
                const severity = e.features[0].properties.severityInfo;
                const event = e.features[0].properties.event;

                new maplibregl.Popup()
                    .setLngLat(e.lngLat)
                    .setHTML(`<div class="block" style="margin:10px"><h2 class="title" style="font-size:18px;">${description}</h2> <h2 class="subtitle" style="font-size:14px;">${event}</h2> <hr> <p>${severity}</p></div>`)
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
                .setHTML(`
                        <div class="block" style="margin:10px; width:200px">
                            <h2 class="title" style="font-size:18px;">${city_name}</h2> 
                            <h2 class="subtitle" style="font-size:14px;">${condition_desc}</h2> 
                            <hr> 
                            <p><b>Min Temperature: </b>${min_temp} °C</p> 
                            <p><b>Max Temperature: </b>${max_temp} °C</p> 
                        </div>`)
                .addTo(forecast_map);
        })
        //  i am here    

        // Change it back to a pointer when it leaves.
        forecast_map.on("mouseleave", "city-forecasts", () => {
            popup.remove()
            forecast_map.getCanvas().style.cursor = "";
        });


    })

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