class BoundaryIDWidget {
    constructor(options) {
        this.geomInput = $('#' + options.id);
        this.options = options
        this.initialValue = this.geomInput.val()
        if (this.options.resize_trigger_selector) {
            this.resizeTriggerEls = $(this.options.resize_trigger_selector)
        }
        this.boundaryInfoUrl = this.geomInput.data("boundaryinfourl")

        this.init()
    }

    init() {

        // Admin level selector
        const adminLevelInputId = this.options.id.replace("geom", "admin_level")
        this.adminLevelSelector = $('#' + adminLevelInputId);
        if (this.adminLevelSelector) {
            this.adminLevelSelector.on("change", (e) => {
                this.onAdminLevelSelectorChange()
            })
        }

        // area description input selector
        const areaDescInputId = this.options.id.replace("geom", "area_desc")
        this.areaDescInput = $('#' + areaDescInputId);

        this.emptyGeojsonData = {type: "Feature", "geometry": {type: "Polygon", coordinates: []}}

        this.initMap().then(() => {

            if (this.resizeTriggerEls && this.resizeTriggerEls.length > 0) {
                for (let i = 0; i < this.resizeTriggerEls.length; i++) {
                    const $el = $(this.resizeTriggerEls[i]);
                    $el.on('click', () => {
                        this.fitBounds()
                    })
                }
            }

            this.fetchAndFitBounds()

            this.initLayer()
            this.initAdmBoundary()

            this.initFromState()

        })
    }

    initAdmBoundary() {
        if (this.boundaryInfoUrl) {
            fetch(this.boundaryInfoUrl).then(res => res.json()).then(boundaryInfo => {
                console.log(boundaryInfo)
                const {tiles_url, detail_url, country_bounds} = boundaryInfo

                if (!tiles_url || !detail_url || !country_bounds) {
                    return
                }

                this.boundaryTilesUrl = tiles_url
                this.boundaryDetailUrl = detail_url
                this.countriesBounds = country_bounds

                this.addAdminBoundaryLayer()

                if (this.countriesBounds) {
                    const bounds = [[this.countriesBounds[0], this.countriesBounds[1]], [this.countriesBounds[2], this.countriesBounds[3]]]
                    this.map.fitBounds(bounds)
                }
            })
        }
    }



    setState(newState) {
        this.geomInput.val(newState);
    };

    getState() {
        return this.geomInput.val();
    };

    getValue() {
        return this.geomInput.val();
    };


    fitBounds() {
        if (this.map) {
            this.map.resize()
            const feature = this.getValueParsed()

            if (!window.document.fullscreenElement) {
                if (feature) {
                    const bounds = turf.bbox(feature)
                    this.map.fitBounds([[bounds[0], bounds[1]], [bounds[2], bounds[3]]])
                } else {
                    if (this.countriesBounds) {
                        const bounds = [[this.countriesBounds[0], this.countriesBounds[1]], [this.countriesBounds[2], this.countriesBounds[3]]]
                        this.map.fitBounds(bounds)
                    }
                }
            }
        }
    }

    fetchAndFitBounds() {
        if (this.boundaryInfoUrl) {
            fetch(this.boundaryInfoUrl)
                .then(response => response.json())
                .then(data => {
                    const {country_bounds} = data
                    if (country_bounds) {
                        this.countriesBounds = country_bounds
                    }
                    this.fitBounds()
                })
                .catch((error) => {
                    console.error('Error:', error);
                });
        }
    }


    async initMap() {
        const defaultStyle = {
            'version': 8, 'sources': {
                'osm': {
                    'type': 'raster', 'tiles': ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"]
                }, 'wikimedia': {
                    'type': 'raster', 'tiles': ["https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png"]
                }
            }, 'layers': [{
                'id': 'osm', 'source': 'osm', 'type': 'raster', 'minzoom': 0, 'maxzoom': 22
            }]
        }
        // initialize map
        this.map = new maplibregl.Map({
            container: this.options.map_id, style: defaultStyle, doubleClickZoom: false, scrollZoom: false,
        });


        this.map.addControl(new maplibregl.NavigationControl({
            showCompass: false,
        }), "bottom-right");

        this.map.addControl(new maplibregl.FullscreenControl());

        await new Promise((resolve) => this.map.on("load", resolve));
    }

    initLayer() {
        // add source
        this.map.addSource("polygon", {
            'type': 'geojson', data: this.emptyGeojsonData
        })

        // add layer
        this.map.addLayer({
            'id': 'polygon', 'type': 'fill', 'source': 'polygon', 'layout': {}, 'paint': {
                'fill-color': 'black', 'fill-opacity': 0.8, "fill-outline-color": "#000",
            }
        });
    }

    setSourceData(featureGeom) {
        if (featureGeom) {

            // truncate the coordinates to 6 decimal places
            turf.truncate(featureGeom, {
                precision: 6, coordinates: 2, mutate: true
            })

            // add data to source
            this.map.getSource("polygon").setData(featureGeom)

            // fit map to bounds
            const bbox = turf.bbox(featureGeom)
            const bounds = [[bbox[0], bbox[1]], [bbox[2], bbox[3]]]
            this.map.fitBounds(bounds, {padding: 50})

            // set state
            const geomString = JSON.stringify(featureGeom)
            this.setState(geomString)
            // clear any map error
            this.hideWarnings()

        } else {

            // clear source data
            this.map.getSource("polygon").setData(this.emptyGeojsonData)

            // clear area desctiption
            this.areaDescInput.val("")

            // set state to empty string
            this.setState("")
        }
    }


    getValueParsed() {
        const value = this.getValue().trim()
        if (value && value !== "") {
            return JSON.parse(value)
        }
        return null
    }


    initFromState() {
        const value = this.getValueParsed()
        if (value) {
            this.setSourceData(value)
        }
    }

    onAdminLevelSelectorChange() {
        this.setSourceData(null)
        const selectedAdminLevel = this.getSelectedAdminLevel()
        const adminFilter = ["==", "level", Number(selectedAdminLevel)]
        const hasSource = this.map.getSource("admin-boundary-source")

        if (hasSource) {
            this.map.setFilter("admin-boundary-fill", adminFilter)
            this.map.setFilter("admin-boundary-line", adminFilter)
        }
    }


    getSelectedAdminLevel() {
        return this.adminLevelSelector.find(":checked").val()
    }

    addAdminBoundaryLayer() {
        const selectedAdminLevel = this.getSelectedAdminLevel()
        const adminFilter = ["==", "level", Number(selectedAdminLevel)]

        // add source
        this.map.addSource("admin-boundary-source", {
            type: "vector", tiles: [this.boundaryTilesUrl],
        })

        // add layer
        this.map.addLayer({
            'id': 'admin-boundary-fill',
            'type': 'fill',
            'source': 'admin-boundary-source',
            "source-layer": "default",
            "filter": adminFilter,
            'paint': {
                'fill-color': "#fff", 'fill-opacity': 0,
            }
        });

        this.map.addLayer({
            'id': 'admin-boundary-line',
            'type': 'line',
            'source': 'admin-boundary-source',
            "source-layer": "default",
            "filter": adminFilter,
            'paint': {
                "line-color": "#444444", "line-width": 0.7,
            }
        });

        this.map.on('mouseenter', 'admin-boundary-fill', () => {
            this.map.getCanvas().style.cursor = 'pointer'
        })
        this.map.on('mouseleave', 'admin-boundary-fill', () => {
            this.map.getCanvas().style.cursor = ''
        })

        this.map.on('click', 'admin-boundary-fill', (e) => {
            const feat = e.features[0]
            if (feat) {
                const {id} = feat.properties

                if (id) {
                    fetch(`${this.boundaryDetailUrl}/${id}`)
                    .then(res => res.json()).then(boundary => {
                        const {feature, level} = boundary
                        const name = boundary[`name_${level}`]

                        if (name) {
                            this.areaDescInput.val(name)
                        }

                        this.setSourceData(feature)
                    }).catch(error => {
                        console.error('Error:', error);
                    });
                }
            }
        });
    }


    createWarningNotificationEl(message, options) {
        const el = document.createElement("div")
        el.className = "notification is-warning map-error"
        el.innerHTML = `
        <div class="notification-content">
            <span class="icon">
              <svg class="icon icon-warning messages-icon" aria-hidden="true">
                <use href="#icon-warning"></use>
               </svg>
            </span>
            <span class="message">${message}</span>
        </div>
    `

        return el
    }

    showWarning(message, options) {
        const notificationEl = this.createWarningNotificationEl(message, options)
        const mapContainer = this.map.getContainer()
        mapContainer.appendChild(notificationEl)
    }

    hideWarnings() {
        const mapContainer = this.map.getContainer()
        mapContainer.querySelectorAll(".map-error").forEach((el) => {
            el.remove()
        })
    }

}


