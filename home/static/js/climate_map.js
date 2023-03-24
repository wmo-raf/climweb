// window.onload = function () {
$(document).ready(function() {
    
        // code to be executed when the DOM is ready
    function roundToNearestHour(date) {
        const hours = date.getHours();
        const roundedHours = Math.ceil(hours / 3) * 3; // Multiples of 3
        date.setMinutes(date.getMinutes() + 30);
        date.setHours(roundedHours)
        date.setMinutes(0, 0, 0);

        return date;
    }

    function subtractHours(date, hours) {
        date.setHours(date.getHours() - hours);
        return date;
    }

    

    const displayTime = new Date()
    const wmsTime = roundToNearestHour(displayTime).toISOString()

    wms_layers.map(layer =>{
        if(layer.category_id == 1){
            console.log(layer)
          return $('.layer-list-items').append(
            `
            <h2 id="${layer.id}"
            class="layer-item subtitle {% if wms == self.get_wms_layers.wms_layers|first %}active{% endif %} ">
            ${layer.title}
            </h2>
            `
          )
        }
      } )
    
      $('#floating-legend').html(`
      <p style="font-weight:600; font-size:14px;margin-bottom:0" class="title">${wms_layers[0].title}</p>
      <p style="margin:0;font-size:12px;" class="subtitle">${wms_layers[0].subtitle}</p>
      <p style="margin:0;font-size:12px;" class="subtitle"><b>Period:</b> ${displayTime} </p>
    
      <div style="width: 100%;
          height: 0.3em;
          position: relative;
          margin-bottom:2em;
          background: linear-gradient(to right,${wms_layers[0].legend_colors.map(legend => legend.item_color)});
        ">
        ${wms_layers[0].legend_colors.map((legend, i) => `<span class="stop-label" style="left: calc( (100% / ${wms_layers[0].legend_colors.length}) * (${i}) )">${legend.item_val}</span>`).join(" ")} </div>`)
    
        
      $('.category-btn').click(function() {
        $('.category-btn').removeClass('is-info')
        $('.category-btn').addClass('is-light')
        $(this).removeClass('is-light')
        $(this).addClass('is-info')
        $('.layer-list-items').html('')
        
        wms_layers.filter(layer => layer.category_id == this.id).map(layer => {
          return $('.layer-list-items').append(
            `
            <h2 id="${layer.id}"
            class="layer-item subtitle ">
            ${layer.title}
            </h2>
            `
          )
      
        })
    
      });

    const climateMap = new maplibregl.Map({
        container: "climate-map", // container ID
        style: basemap,
        center: [30.019531249998607, 16.130262012034265], // starting position [lng, lat]
        zoom: 4.2, // starting zoom
        scrollZoom: false,
    });

    // Add zoom and rotation controls to the map.
    climateMap.addControl(new maplibregl.NavigationControl(), 'bottom-right');

    climateMap.on("load", () => {



        if (country_geom) {
            const wktWithoutSrids = country_geom.replace(/^SRID=\d+;/, "");

            // define a regular expression pattern to match the coordinates
            const pattern = /\(([^()]+)\)/g;

            // create an array to store the coordinates
            let coordinates = [];

            // loop through each match of the pattern and extract the coordinates
            let match;
            while ((match = pattern.exec(wktWithoutSrids)) !== null) {
                // split the match into individual coordinates
                const coords = match[1].trim().split(', ');
                // convert the coordinates to an array of numbers
                const coordsArray = coords.map(coord => coord.split(" ").map(co => Number(co)));
                // add the coordinates to the array
                coordinates.push(coordsArray);

            }

            var multipolyFeature = {
                type: "Feature",
                geometry: {
                    type: "MultiPolygon",
                    coordinates: [coordinates],
                },
            }

            // output the coordinates to the console
            var bounds = turf.bbox({
                type: "FeatureCollection",
                features: [multipolyFeature],
            });
            climateMap.fitBounds(bounds, { padding: 20 });

        }

        const styleLayers = climateMap.getStyle().layers;

        // Find the index of the first symbol layer in the map style.
        let admin0Boundaries, admin1Boundaries, cityLabel,countryLabel;
        for (const l of styleLayers) {
            if (l.id === "1") {
                admin0Boundaries = l.id;
            }
            if (l.id === "8") {
                admin1Boundaries = l.id;
            }
            if (l.id === "country_label") {
                countryLabel = l.id;
            }
            if (l.id === "place_label_city") {
                cityLabel = l.id;
            }
        }

      
        // Get all the items
        const layer_items = document.querySelectorAll('.layer-item');

       

       


        fetch(`http://20.56.94.119/api/geostore/admin/${countryIso}?thresh=0.005`)
            .then(response => response.json())
            .then(data => {
                climateMap.addSource('wms-source', {
                    type: "raster",
                    tiles: [
                        `${wms_layers[0].base_url}?service=WMS&request=GetMap&version=${wms_layers[0].version}&width=${wms_layers[0].width}&height=${wms_layers[0].height}&styles=&transparent=${wms_layers[0].transparent}&srs=${wms_layers[0].srs}&bbox={bbox-epsg-3857}&format=${wms_layers[0].format}&time=${wmsTime}&layers=${wms_layers[0].layers__name}&geojson_feature_id=${data.data.id}&canClipToGeom=true`,
                    ],
                    minzoom: 3,
                    maxzoom: 12,
                    'tileSize': 256

                });

                climateMap.addLayer({
                    'id': 'wms-layer',
                    'type': 'raster',
                    'source': 'wms-source',
                    //'paint': {
                    //  'raster-opacity': 0.8
                    //}
                }, cityLabel,countryLabel,admin1Boundaries, admin0Boundaries, );

                // Loop through the items and add a click event listener to each
                layer_items.forEach(item => {

                    item.addEventListener('click', () => {
                        // Remove the active class from all items

                        layer_items.forEach(item => {
                            //  const item_id = item.id;

                            item.classList.remove('active');

                        });
                        wms_layers.map(layer => {

                            if (layer.id == item.id) {
                                $('#floating-legend').html(`
                                    <p style="font-weight:600; font-size:14px;margin-bottom:0" class="title">${layer.title}</p>
                                        <p style="margin:0;font-size:12px;" class="subtitle">${layer.subtitle}</p>
                                        <p style="margin:0;font-size:12px;" class="subtitle"><b>Period:</b> ${displayTime}</p>
                    
                                        <div style="width: 100%;
                                                            height: 0.3em;
                                                            position: relative;
                                                            margin-bottom:2em;
                                                            background: linear-gradient(to right, ${layer.legend_colors.map(legend => legend.item_color)});
                                                        ">
                                                        ${layer.legend_colors.map((legend, i) => `<span class="stop-label" style="left: calc( (100% / ${layer.legend_colors.length}) * (${i}) )">${legend.item_val}</span>`).join(" ")}</div> `)

                                if (climateMap.getLayer("wms-layer")) {
                                    climateMap.removeLayer("wms-layer");
                                }
                                if (climateMap.getSource("wms-source")) {
                                    climateMap.removeSource("wms-source");
                                }

                                climateMap.addSource('wms-source', {
                                    type: "raster",
                                    tiles: [
                                        `${layer.base_url}?service=WMS&request=GetMap&version=${layer.version}&width=${layer.width}&height=${layer.height}&styles=&transparent=${layer.transparent}&srs=${layer.srs}&bbox={bbox-epsg-3857}&format=${layer.format}&time=${wmsTime}&layers=${layer.layers__name}&geojson_feature_id=${data.data.id}&canClipToGeom=true`,
                                    ],
                                    minzoom: 3,
                                    maxzoom: 12,
                                    'tileSize': 256

                                });

                                climateMap.addLayer({
                                    'id': 'wms-layer',
                                    'type': 'raster',
                                    'source': 'wms-source',
                                    //'paint': {
                                    //  'raster-opacity': 0.8
                                    //}
                                }, cityLabel, countryLabel, admin1Boundaries, admin0Boundaries);
                            }

                        })
                        // Add the active class to the clicked item
                        item.classList.add('active');

                    })

                })
            })

    })
// }

})


