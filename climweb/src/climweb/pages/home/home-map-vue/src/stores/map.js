// stores/map.js
import {defineStore} from 'pinia';
import {computed, ref} from 'vue';

export const useMapStore = defineStore('map', () => {
            const layers = ref({
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
                    dateFormat: "yyyy-MM-dd HH:mm",
                    icon: "icon-heavy-rain",
                    multiTemporal: true,
                },
            });

            const sortedFixedLayers = computed(() => {
                return Object.values(layers.value)
                    .filter((layer) => layer.enabled && layer.homeMapLayerType === "fixed")
                    .sort((a, b) => a.position - b.position);
            });

            function updateLayerState(layerId, enabled) {
                if (layers.value[layerId]) {
                    layers.value[layerId].enabled = enabled;
                }
            }

            function updateLayerVisibility(layerId, visible) {
                if (layers.value[layerId]) {
                    layers.value[layerId].visible = visible;
                }
            }

            const setWeatherForecastLayerDateFormat = (dateFormat) => {
                if (layers.value["weather-forecast"]) {
                    layers.value["weather-forecast"].dateFormat = dateFormat;
                }
            }


            const timeLayerDates = ref({})
            const selectedTimeLayerDate = ref({})
            const activeTimeLayer = ref(null)

            const setTimeLayerDates = (layerId, dates) => {
                if (!timeLayerDates.value[layerId]) {
                    timeLayerDates.value[layerId] = ref([]);
                }

                timeLayerDates.value[layerId].value = dates;
            }

            const setSelectedTimeLayerDate = (layerId, date) => {
                selectedTimeLayerDate.value[layerId] = date;
            }

            const setActiveTimeLayer = (layerId) => {
                activeTimeLayer.value = layerId;
            }

            const getLayerById = (layerId) => {
                return layers.value[layerId];
            }

            return {
                layers,
                sortedFixedLayers,
                timeLayerDates,
                selectedTimeLayerDate,
                activeTimeLayer,
                setTimeLayerDates,
                setSelectedTimeLayerDate,
                updateLayerState,
                updateLayerVisibility,
                setActiveTimeLayer,
                setWeatherForecastLayerDateFormat,
                getLayerById
            };
        }
    )
;