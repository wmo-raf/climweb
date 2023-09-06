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

    const map = new maplibregl.Map({
        container: "home-map", // container ID
        style: defaultStyle,
        center: [30.019531249998607, 16.130262012034265], // starting position [lng, lat]
        zoom: 4.2, // starting zoom
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
        const paramValues = dataParams.reduce((all, param) => {
            if (props[param.parameter]) {
                all[param.name] = `${props[param.parameter]} ${param.parameter_unit}`
            }
            return all
        }, {})

        const cityName = props.city_name;
        const condition = props.condition;
        const analysis_url = "{% url city_analysis %}"

        console.log(analysis_url)

        let values = Object.keys(paramValues).reduce((all, key) => {
            all = all + `<p class="py-0" style="padding:0.5em 0"><b>${key}: </b>${paramValues[key]}</p>`
            return all
        }, "")

        return `<div class="block" style="margin:10px; width:200px">
            <h2 class="title" style="font-size:18px;">${cityName}</h2>
            <h2 class="subtitle mb-0" style="font-size:14px;">${condition}</h2>

            <a class="button is-small is-light mt-2" target="_blank" rel="noopender noreferrer" href="city_analysis/${cityName}"> <span>Analysis </span>
            <span class="icon">
                <i class="fa-solid fa-arrow-trend-up"></i>
            </span> </a>
            <hr>
            ${values}

            
        </div>`
    }

    function updateSourceData(data) {
        map.getSource('city-forecasts').setData(data);
    }

    map.on("load", () => {

        if (country_info && country_info.bbox) {

            const bbox = country_info.bbox

            map.fitBounds(bbox, {padding: 50});
        }

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

            // When a click event occurs on a feature in the places layer, open a popup at the
            // location of the feature, with description HTML from its properties.
            map.on("click", "alert-areas-layer", (e) => {
                // Copy coordinates array.

                console.log(e.features[0].properties)
                const description = e.features[0].properties.areaDesc;
                const severity = e.features[0].properties.severity;
                const event = e.features[0].properties.event;

                new maplibregl.Popup()
                    .setLngLat(e.lngLat)
                    .setHTML(`<div class="block" style="margin:10px"><h2 class="title" style="font-size:15px;">${description}</h2> <h2 class="subtitle" style="font-size:14px;">${event}</h2> <hr> <p>${severity} severity</p> </a></div>`)
                    .addTo(map);

                 
            });

            // Change the cursor to a pointer when the mouse is over the places layer.
            map.on("mouseenter", "alert-areas-layer", () => {
                map.getCanvas().style.cursor = "pointer";
            });

            // Change it back to a pointer when it leaves.
            map.on("mouseleave", "alert-areas-layer", () => {
                map.getCanvas().style.cursor = "";
            });
        }

        map.addSource("city-forecasts", {
            type: "geojson",
            data: {type: "FeatureCollection", features: []}
        })

        map.addLayer({
            "id": "city-forecasts",
            "type": "symbol",
            "layout": {
                'icon-image': ['get', 'condition_icon'],
                'icon-size': 0.3,
                'icon-allow-overlap': true
            },
            source: "city-forecasts"
        })


        // When a click event occurs on a feature in the places layer, open a popup at the
        // location of the feature, with description HTML from its properties.
        

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
            new maplibregl.Popup().setLngLat(e.lngLat)
                .setHTML(getPopupHTML(feature.properties))
                .addTo(map);


        })

        

        // Change it back to a pointer when it leaves.
        map.on("mouseleave", "city-forecasts", () => {
            map.getCanvas().style.cursor = "";
        });

        const initDate = document.getElementById("daily_forecast");

        if (initDate.value) {
            setForecastData(initDate.value)
        }
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
                        if (!map.hasImage(icon.properties.condition_icon)) {
                            return map.addImage(`${icon.properties.condition_icon}`, img)
                        }

                    }
                    img.src = `${static_path}${icon.properties.condition_icon}`
                    return img.src

                })
                // Access and use the data as needed                
                updateSourceData({
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
        const valueSelected = this.value;

        setForecastData(valueSelected)
    });

});