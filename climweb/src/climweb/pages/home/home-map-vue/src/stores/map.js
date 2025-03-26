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

    return {
        layers,
        sortedFixedLayers,
        sortedDynamicLayers,
        timeLayerDates,
        selectedTimeLayerDateIndex,
        activeTimeLayer,
        setTimeLayerDates,
        setSelectedTimeLayerDateIndex,
        updateLayerState,
        updateLayerVisibility,
        setActiveTimeLayer,
        setWeatherForecastLayerDateFormat,
        getLayerById,
        addLayer,
    };
});