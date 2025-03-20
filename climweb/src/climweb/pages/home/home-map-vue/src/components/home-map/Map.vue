<template>
  <div ref="mapContainer" class="map-container"></div>
  <div class="zoom-controls">
    <button @click="zoomIn">+</button>
    <button @click="zoomOut">−</button>
  </div>
  <div class="basemap-control">
    <div class="basemap-icon icon" @click="toggleBaseMapChooser">
      <svg>
        <use xlink:href="#icon-layers"></use>
      </svg>
    </div>
    <Popover ref="basemapChooserRef">
      Hello
    </Popover>
  </div>

  <div class="fixed-layer-control">
    <LayerItem v-for="layer in sortedFixedLayers" :key="layer.id" :title="layer.title" :active="layer.active"
               :layer-type="layer.layerType" :position="layer.position" :id="layer.id"
               @update:toggleLayer="handleLayerToggle"/>
  </div>
  <div class="dynamic-layer-control">
  </div>


  <div class="date-navigator-control">
    <DateNavigator :dates="dateList" @update:selectedDate="handleDateChange"/>
  </div>


</template>

<script setup>
import maplibregl from "maplibre-gl";
import {computed, onMounted, onUnmounted, ref, shallowRef} from 'vue';
import Popover from 'primevue/popover';
import {bbox as turfBbox} from "@turf/bbox";
import LayerItem from "./LayerItem.vue";

import 'maplibre-gl/dist/maplibre-gl.css';

import DateNavigator from "./DateNavigator.vue";

const props = defineProps({
  mapSettingsUrl: {
    type: String,
    required: true
  },
  initialBounds: {
    type: String,
    required: false
  },
})

const mapContainer = shallowRef(null);
const basemapChooserRef = ref()
let map;
let forecastData = ref([])

const fixedLayers = ref({
  "weather-warnings": {
    id: "weather-warnings",
    layerType: "fixed",
    title: "Weather Warnings",
    position: 1,
    active: false
  },
  "weather-forecast": {
    id: "weather-forecast",
    layerType: "fixed",
    title: "Weather Forecast",
    position: 2,
    active: false,
  }
});


const sortedFixedLayers = computed(() => {
  return Object.values(fixedLayers.value).sort((a, b) => a.position - b.position);
});


const dateList = ref(["2025-03-17 13:00", "2025-03-18 14:00", "2025-03-19 15:00"]);

const handleDateChange = (newDate) => {
  console.log("Selected Date:", newDate);
};

const handleLayerToggle = (layer) => {
  const {layerId, active} = layer

  const mapLayer = map.getLayer(layerId)

  if (mapLayer) {
    if (active) {
      map.setLayoutProperty(mapLayer.id, "visibility", "visible")
    } else {
      map.setLayoutProperty(mapLayer.id, "visibility", "none")
    }
  }
}


const fetchMapSettings = async () => {
  return fetch(props.mapSettingsUrl).then(response => response.json())
}

onMounted(() => {
  const mapInitOptions = {
    container: mapContainer.value,
    style: "https://tiles.basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
    center: [0, 0],
    zoom: 4,
    scrollZoom: false
  }

  if (props.initialBounds) {
    try {
      const bounds = JSON.parse(props.initialBounds)
      mapInitOptions.bounds = [[bounds[0], bounds[1]], [bounds[2], bounds[3]]]
      mapInitOptions.fitBoundsOptions = {padding: 20}
    } catch (e) {
      console.log("Error parsing initial bounds", e)
    }
  }

  map = new maplibregl.Map({
    ...mapInitOptions
  });

  map.on("load", () => {
    fetchMapSettings().then(mapSettings => {
      initializeMapLayers(mapSettings);
    });
  });
})

onUnmounted(() => {
  map?.remove();
})

const zoomIn = () => {
  map?.zoomIn();
};

const zoomOut = () => {
  map?.zoomOut();
};

const toggleBaseMapChooser = (event) => {
  basemapChooserRef.value.toggle(event)
};

const initializeMapLayers = (mapSettings) => {
  const {
    zoomLocations,
    boundaryTilesUrl,
    weatherIconsUrl,
    forecastSettingsUrl,
    homeMapAlertsUrl,
    homeForecastDataUrl,
    capGeojsonUrl,
    forecastClusterConfig,
  } = mapSettings


  addBoundaryLayer(boundaryTilesUrl);

  addWarningsLayer(capGeojsonUrl);

  initializeCityForecast(homeForecastDataUrl, weatherIconsUrl, forecastClusterConfig);
}

const addBoundaryLayer = (boundaryTilesUrl) => {
  // add source
  map.addSource("admin-boundary-source", {
    type: "vector", tiles: [boundaryTilesUrl],
  })
  // add layer
  map.addLayer({
    'id': 'admin-boundary-fill',
    'type': 'fill',
    'source': 'admin-boundary-source',
    "source-layer": "default",
    "filter": ["==", "level", 0],
    'paint': {
      'fill-color': "#fff", 'fill-opacity': 0,
    }
  });

  map.addLayer({
    'id': 'admin-boundary-line',
    'type': 'line',
    'source': 'admin-boundary-source',
    "source-layer": "default",
    "filter": ["==", "level", 0],
    'paint': {
      "line-color": "#C0FF24", "line-width": 1, "line-offset": 1,
    }
  });

  map.addLayer({
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


const addWarningsLayer = (capGeojsonUrl) => {

  fetch(capGeojsonUrl).then(res => res.json()).then(alertsGeojson => {
    if (alertsGeojson.features.length > 0) {
      const bounds = turfBbox(alertsGeojson);

      // fit map to alert bounds
      map.fitBounds(bounds, {padding: 50});

      // add cap alerts layer
      map.addSource("weather-warnings", {
        type: "geojson",
        data: alertsGeojson,
      });

      // add layer
      map.addLayer({
        id: "weather-warnings",
        type: "fill",
        source: "weather-warnings",
        paint: {
          "fill-color": ["case", ["==", ["get", "severity"], "Extreme"], "#d72f2a", ["==", ["get", "severity"], "Severe"], "#f89904", ["==", ["get", "severity"], "Moderate"], "#e4e616", ["==", ["get", "severity"], "Minor"], "#53ffff", ["==", ["get", "severity"], "Unknown"], "#3366ff", "black",],
          "fill-opacity": 0.7,
          "fill-outline-color": "#000",
        },
      }, "weather-forecast");

      if (fixedLayers.value["weather-warnings"]) {
        fixedLayers.value = {
          ...fixedLayers.value,
          "weather-warnings": {
            ...fixedLayers.value["weather-warnings"],
            active: true,
          },
        };
      }
    }
  })
}

const initializeCityForecast = (homeForecastDataUrl, weatherIconsUrl, forecastClusterConfig) => {
  // add city forecast source
  map.addSource("weather-forecast", {
    type: "geojson", data: {type: "FeatureCollection", features: []}, ...forecastClusterConfig,
  })

  // add city forecast layer
  map.addLayer({
    id: "weather-forecast",
    type: "symbol",
    layout: {
      'icon-image': ['get', 'condition'], 'icon-size': 0.3, 'icon-allow-overlap': true
    },
    source: "weather-forecast"
  })
  // fetch city forecast data
  fetch(homeForecastDataUrl).then(res => res.json()).then(data => {
    // get and set weather icons
    getWeatherIcons(weatherIconsUrl)

    // set city forecast data
    setCityForecastData(data)


    if (fixedLayers.value["weather-forecast"]) {
      fixedLayers.value = {
        ...fixedLayers.value,
        "weather-forecast": {
          ...fixedLayers.value["weather-forecast"],
          active: true,
        },
      };
    }


  })
}

const getWeatherIcons = (weatherIconsUrl) => {
  fetch(weatherIconsUrl).then(response => response.json()).then(icons => {
    if (icons && Array.isArray(icons))
      icons.forEach(icon => {
        map.loadImage(icon.url).then(image => {
          map.addImage(icon.id, image.data);
        });
      });
  });
}

const setCityForecastData = (data) => {
  const {multi_period: isMultiPeriod, data: apiForecastData} = data
  forecastData.value = apiForecastData
  const dates = forecastData.value.map(d => d.datetime)
  const selectedDate = dates?.[0]
  updateMapCityForecastData(selectedDate)
}

const updateMapCityForecastData = (date) => {
  const selectedDateData = forecastData.value.find(d => d.datetime === date)

  if (selectedDateData) {
    map.getSource("weather-forecast").setData(selectedDateData)
  }
}


</script>
<style scoped>
.map-container {
  width: 100%;
  height: 100%;
}

.zoom-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.zoom-controls button {
  width: 30px;
  height: 30px;
  border: none;
  border-radius: 50%;
  background: gray;
  color: #fff;
  font-size: 20px;
  cursor: pointer;
}

.zoom-controls button:hover {
  background: #666;
}

.basemap-control {
  position: absolute;
  top: 90px;
  right: 10px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.basemap-icon {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: gray;
  cursor: pointer;
}

.basemap-icon svg {
  height: 16px;
  width: 16px;
  fill: #fff;
}

.fixed-layer-control {
  position: absolute;
  top: 20px;
  left: 30px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dynamic-layer-control {
  position: absolute;
  bottom: 20px;
  left: 30px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.date-navigator-control {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px;
}

</style>