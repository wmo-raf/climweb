import {defineStore} from "pinia";
import {computed, reactive, ref} from "vue";

export const useMapStore = defineStore("map", () => {
    const layers = reactive({
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
            position: 2,
            visible: false,
            enabled: false,
            dateFormat: {
                currentTime: "yyyy-MM-dd HH:mm",
            },
            icon: "icon-heavy-rain",
            multiTemporal: true,
        },
    });
    const loading = ref(false);

    const sortedFixedLayers = computed(() => {
        return Object.values(layers)
            .filter((layer) => layer.enabled && layer.homeMapLayerType === "fixed")
            .sort((a, b) => a.position - b.position);
    });
    const sortedDynamicLayers = computed(() => {
        return Object.values(layers)
            .filter((layer) => layer.enabled && layer.homeMapLayerType === "dynamic")
            .sort((a, b) => a.position - b.position);
    });

    const timeLayerDates = ref({});
    const selectedTimeLayerDateIndex = ref({});
    const activeTimeLayer = ref(null);

    const forecastSettings = ref({});
    const setForecastSettings = (settings) => {
        forecastSettings.value = settings;
    }

    const basemaps = ref([
        {
            "label": "Voyager",
            "value": "voyager",
        },
        {
            "label": "Light",
            "value": "carto-light",
        },
        {
            "label": "Dark",
            "value": "carto-dark",
        },
    ])

    const selectedBasemap = ref(basemaps.value[0].value);

    const showBoundary = ref(true);
    const setShowBoundary = (value) => {
        showBoundary.value = value;
    }


    const setSelectedBasemap = (basemap) => {
        if (basemaps.value.some(b => b.value === basemap)) {
            selectedBasemap.value = basemap;
        } else {
            console.error("Invalid basemap selected");
        }
    }


    const setLoading = (isLoading) => {
        loading.value = isLoading;
    }

    const updateLayerState = (layerId, enabled) => {
        if (layers[layerId]) {
            layers[layerId].enabled = enabled;
        } else {
            console.warn(`Layer with ID '${layerId}' not found`);
        }
    };

    const updateLayerVisibility = (layerId, visible) => {
        if (layers[layerId]) {
            layers[layerId].visible = visible;
        } else {
            console.warn(`Layer with ID '${layerId}' not found`);
        }
    };

    const updateLayerTitle = (layerId, title) => {
        if (layers[layerId]) {
            layers[layerId].title = title;
        } else {
            console.warn(`Layer with ID '${layerId}' not found`);
        }
    }

    const setWeatherForecastLayerDateFormat = (dateFormat) => {
        if (layers["weather-forecast"]) {
            layers["weather-forecast"].dateFormat = dateFormat;
        }
    };

    const setTimeLayerDates = (layerId, dates) => {
        timeLayerDates.value = {...timeLayerDates.value, [layerId]: dates};
    };

    const setSelectedTimeLayerDateIndex = (layerId, index) => {
        selectedTimeLayerDateIndex.value = {...selectedTimeLayerDateIndex.value, [layerId]: index};
    };

    const setActiveTimeLayer = (layerId) => {
        activeTimeLayer.value = layerId;
    };

    const getLayerById = (layerId) => {
        return layers[layerId] || null;
    };

    const addLayer = (layer) => {
        if (!layer.id || layers[layer.id]) {
            console.error("Invalid or duplicate layer ID");
            return;
        }
        layers[layer.id] = layer;
    };

    const visibleLayers = computed(() => {
        return Object.values(layers).filter((layer) => layer.visible);
    });

    return {
        loading,
        layers,
        sortedFixedLayers,
        sortedDynamicLayers,
        visibleLayers,
        timeLayerDates,
        selectedTimeLayerDateIndex,
        activeTimeLayer,
        basemaps,
        selectedBasemap,
        showBoundary,
        forecastSettings,
        setLoading,
        setTimeLayerDates,
        setSelectedTimeLayerDateIndex,
        updateLayerState,
        updateLayerVisibility,
        setActiveTimeLayer,
        setWeatherForecastLayerDateFormat,
        getLayerById,
        addLayer,
        setSelectedBasemap,
        setShowBoundary,
        updateLayerTitle,
        setForecastSettings
    };
});