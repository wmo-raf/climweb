<template>
  <div ref="mapContainer" class="map-container"></div>

  <!-- Zoom Controls -->
  <div class="zoom-controls">
    <button @click="zoomIn">+</button>
    <button @click="zoomOut">−</button>
  </div>

  <!-- Basemap Controls -->
  <div class="basemap-control">
    <div class="basemap-icon icon" @click="toggleBaseMapChooser">
      <svg>
        <use xlink:href="#icon-layer-group"></use>
      </svg>
    </div>
    <Popover ref="basemapChooserRef">
      Hello
    </Popover>
  </div>

  <!-- Fixed Layers -->
  <div class="fixed-layer-control">
    <LayerItem
        v-for="layer in mapStore.sortedFixedLayers"
        :key="layer.id"
        :title="layer.title"
        :enabled="layer.enabled"
        :visible="layer.visible"
        :home-map-layer-type="layer.homeMapLayerType"
        :position="layer.position"
        :id="layer.id"
        :icon="layer.icon"
        @update:toggleLayer="handleLayerToggle"
    />
  </div>

  <!-- Date Navigator -->
  <div class="date-navigator-control">
    <DateNavigator/>
  </div>
</template>

<script setup>
import {onMounted, onUnmounted, ref, shallowRef, watch} from 'vue';
import maplibregl from "maplibre-gl";
import {bbox as turfBbox} from "@turf/bbox";
import {useMapStore} from "@/stores/map";
import Popover from 'primevue/popover';
import LayerItem from "./LayerItem.vue";
import DateNavigator from "./DateNavigator.vue";

import 'maplibre-gl/dist/maplibre-gl.css';

const props = defineProps({
  mapSettingsUrl: {
    type: String,
    required: true
  },
  initialBounds: {
    type: String,
    required: false
  },
});

const mapStore = useMapStore();
const mapContainer = shallowRef(null);
const basemapChooserRef = ref();
let forecastData = ref([])
let map;


// Fetch map settings from API
const fetchMapSettings = async () => {
  const response = await fetch(props.mapSettingsUrl);
  return response.json();
};

// Initialize Map
const initializeMap = async () => {
  const mapInitOptions = {
    container: mapContainer.value,
    style: "https://tiles.basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
    center: [0, 0],
    zoom: 4,
    scrollZoom: false,
  };

  if (props.initialBounds) {
    try {
      const bounds = JSON.parse(props.initialBounds);
      mapInitOptions.bounds = [[bounds[0], bounds[1]], [bounds[2], bounds[3]]];
      mapInitOptions.fitBoundsOptions = {padding: 20};
    } catch (e) {
      console.error("Error parsing initial bounds", e);
    }
  }

  map = new maplibregl.Map(mapInitOptions);

  map.on("load", async () => {
    const mapSettings = await fetchMapSettings();
    initializeMapLayers(mapSettings);
  });
};

const initializeMapLayers = (mapSettings) => {
  const {
    boundaryTilesUrl,
    showWarningsLayer,
    capGeojsonUrl,
    showLocationForecastLayer,
    locationForecastDateDisplayFormat,
    homeForecastDataUrl,
    weatherIconsUrl,
    forecastClusterConfig
  } = mapSettings;

  addBoundaryLayer(boundaryTilesUrl);

  if (showWarningsLayer) {
    mapStore.updateLayerState("weather-warnings", true);
    addWarningsLayer(capGeojsonUrl);
  }

  if (showLocationForecastLayer) {
    mapStore.updateLayerState("weather-forecast", true);
    mapStore.setWeatherForecastLayerDateFormat(locationForecastDateDisplayFormat);
    addLocationForecastLayer(homeForecastDataUrl, weatherIconsUrl, forecastClusterConfig)
  }

};

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
      });

      mapStore.updateLayerVisibility("weather-warnings", true);
    }
  })
}


const addLocationForecastLayer = (homeForecastDataUrl, weatherIconsUrl, forecastClusterConfig) => {
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
  });

  fetch(homeForecastDataUrl).then(res => res.json()).then(response => {
    // get and set weather icons
    addWeatherIcons(weatherIconsUrl)
    // set city forecast data
    setCityForecastData(response)

    const {data} = response

    if (data && !!data.length) {
      mapStore.updateLayerVisibility("weather-forecast", true)
    }
  });
}

const addWeatherIcons = (weatherIconsUrl) => {
  fetch(weatherIconsUrl).then(response => response.json()).then(icons => {
    if (icons && Array.isArray(icons))
      icons.forEach(icon => {
        map.loadImage(icon.url).then(image => {
          map.addImage(icon.id, image.data);
        });
      });
  });
}


const setCityForecastData = (apiResponse) => {
  const {multi_period: isMultiPeriod, data: apiForecastData} = apiResponse
  forecastData.value = apiForecastData

  const now = new Date()
  const dates = apiForecastData.reduce((all, d) => {
    const dObj = new Date(d.datetime)
    if (!(isMultiPeriod && dObj.toDateString() === now.toDateString() && dObj.getHours() < now.getHours())) {
      all.push(d.datetime)
    }
    return all
  }, [])

  mapStore.setActiveTimeLayer("weather-forecast")
  mapStore.setTimeLayerDates("weather-forecast", dates)
}

const updateMapCityForecastData = (date) => {

  const selectedDateData = forecastData.value.find(d => d.datetime === date)

  if (selectedDateData) {
    map.getSource("weather-forecast").setData(selectedDateData)
  }
}

// Map Controls
const zoomIn = () => map?.zoomIn();
const zoomOut = () => map?.zoomOut();

const toggleBaseMapChooser = (event) => {
  basemapChooserRef.value.toggle(event);
};

const handleLayerToggle = ({layerId, visible}) => {
  mapStore.updateLayerVisibility(layerId, visible);

  const layer = mapStore.getLayerById(layerId);

  const mapLayer = map.getLayer(layerId);
  if (mapLayer) {
    map.setLayoutProperty(mapLayer.id, "visibility", visible ? "visible" : "none");
  }

  if (layer.multiTemporal) {
    if (visible) {
      mapStore.setActiveTimeLayer(layerId)
    } else {
      mapStore.setActiveTimeLayer(null)
    }
  }
};

watch(mapStore.selectedTimeLayerDate, (newTimeLayerDate) => {
  if (newTimeLayerDate[mapStore.activeTimeLayer]) {
    const date = newTimeLayerDate[mapStore.activeTimeLayer]

    if (mapStore.activeTimeLayer === "weather-forecast") {
      updateMapCityForecastData(date)
    }
  }
});


onMounted(() => initializeMap());
onUnmounted(() => map?.remove());
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