import {defineStore} from 'pinia';

export const useMapStore = defineStore('map', {
    state: () => ({
        loading: false,
        layers: {
            "weather-warnings": {
                id: "weather-warnings",
                homeMapLayerType: "fixed",
                title: "Weather Warnings",
                position: 1,
                visible: false,
                enabled: false,
                icon: "icon-warning",
                multiTemporal: false,
                legendConfig: {
                    type: "basic",
                    title: "Weather Warnings",
                    items: [
                        {name: "Extreme", color: "#d72f2a"},
                        {name: "Severe", color: "#fe9900"},
                        {name: "Moderate", color: "#ff0"},
                        {name: "Minor", color: "#03ffff"},
                    ],
                }
            },
            "weather-forecast": {
                id: "weather-forecast",
                homeMapLayerType: "fixed",
                title: "Weather Forecast",
                position: 0,
                visible: true,
                enabled: true,
                dateFormat: {
                    currentTime: "yyyy-MM-dd HH:mm",
                },
                icon: "icon-heavy-rain",
                multiTemporal: true,
            }
        },
        timeLayerDates: {},
        selectedTimeLayerDateIndex: {},
        activeTimeLayer: null,
        forecastSettings: {},
        zoomLocations: [],
        selectedZoomLocation: null,
        basemaps: [
            {label: "Voyager", value: "voyager"},
            {label: "Light", value: "carto-light"},
            {label: "Dark", value: "carto-dark"},
        ],
        selectedBasemap: "voyager",
        apiBaseMaps: [],
        selectedApiBaseMap: null,
        usingApiStyle: false,
        showBoundary: true,
    }),

    getters: {
        sortedFixedLayers(state) {
            return Object.values(state.layers)
                .filter(layer => layer.enabled && layer.homeMapLayerType === "fixed")
                .sort((a, b) => a.position - b.position);
        },
        sortedDynamicLayers(state) {
            return Object.values(state.layers)
                .filter(layer => layer.enabled && layer.homeMapLayerType === "dynamic")
                .sort((a, b) => a.position - b.position);
        },
        visibleLayers(state) {
            return Object.values(state.layers).filter(layer => layer.visible);
        },
        getApiBaseMapById: (state) => (baseMapId) => {
            return state.apiBaseMaps.find(basemap => basemap.id === baseMapId) || null;
        }
    },

    actions: {
        setLoading(isLoading) {
            this.loading = isLoading;
        },
        setLayerOpacity(layerId, opacity) {
            if (this.layers[layerId]) {
                this.layers[layerId].opacity = opacity;
            }
        },
        updateLayerState(layerId, enabled) {
            if (this.layers[layerId]) {
                this.layers[layerId].enabled = enabled;
            } else {
                console.warn(`Layer with ID '${layerId}' not found`);
            }
        },
        updateLayerVisibility(layerId, visible) {
            if (this.layers[layerId]) {
                this.layers[layerId].visible = visible;
            } else {
                console.warn(`Layer with ID '${layerId}' not found`);
            }
        },
        updateLayerTitle(layerId, title) {
            if (this.layers[layerId]) {
                this.layers[layerId].title = title;
            } else {
                console.warn(`Layer with ID '${layerId}' not found`);
            }
        },
        setWeatherForecastLayerDateFormat(dateFormat) {
            if (this.layers["weather-forecast"]) {
                this.layers["weather-forecast"].dateFormat = dateFormat;
            }
        },
        setTimeLayerDates(layerId, dates) {
            this.timeLayerDates = {...this.timeLayerDates, [layerId]: dates};
        },
        setSelectedTimeLayerDateIndex(layerId, index) {
            this.selectedTimeLayerDateIndex = {...this.selectedTimeLayerDateIndex, [layerId]: index};
        },
        setActiveTimeLayer(layerId) {
            this.activeTimeLayer = layerId;
        },
        getLayerById(layerId) {
            return this.layers[layerId] || null;
        },
        addLayer(layer) {
            if (!layer.id || this.layers[layer.id]) {
                console.error("Invalid or duplicate layer ID");
                return;
            }
            this.layers[layer.id] = layer;
        },
        setForecastSettings(settings) {
            this.forecastSettings = settings;
        },
        setZoomLocations(locations) {
            this.zoomLocations = locations;
        },
        setSelectedZoomLocation(locationId) {
            this.selectedZoomLocation = locationId;
        },
        setSelectedBasemap(basemap) {
            if (this.basemaps.some(b => b.value === basemap)) {
                this.selectedBasemap = basemap;
            } else {
                console.error("Invalid basemap selected");
            }
        },
        setShowBoundary(value) {
            this.showBoundary = value;
        },
        setApiBaseMaps(baseMaps) {
            this.apiBaseMaps = baseMaps;
        },
        setSelectedApiBaseMap(baseMapId) {
            this.selectedApiBaseMap = baseMapId;
        },
        getSelectedApiBaseMap() {
            return this.apiBaseMaps.find(basemap => basemap.id === this.selectedApiBaseMap) || null;
        },
        setUsingApiStyle(value) {
            this.usingApiStyle = value;
        },
    },
});
