<script setup>
import {computed, nextTick, onMounted, onUnmounted, ref, shallowRef, watch} from 'vue';
import maplibregl from "maplibre-gl";
import {bbox as turfBbox} from "@turf/bbox";

import {useMapStore} from "@/stores/map";
import {getRasterLayerConfig, getVectorTileLayerConfig, updateSourceTileUrl, updateTileUrl} from "@/utils/map";
import {getTimeFromList} from "@/utils/date";
import {getTimeValuesFromWMS} from "@/utils/wms";

import Popover from 'primevue/popover';
import LayerItem from "./LayerItem.vue";
import DateNavigator from "./DateNavigator.vue";
import Legend from "./legend/Legend.vue";
import MapOptions from "./MapOptions.vue";
import CAPWarningPopup from "./popup/CAPWarningPopup.vue";
import LocationForecastPopup from "./popup/LocationForecastPopup.vue";

import 'maplibre-gl/dist/maplibre-gl.css';
import {defaultMapStyle} from "@/utils/basemap.js";


const props = defineProps({
  mapSettingsUrl: {
    type: String,
    required: true
  },
  initialBounds: {
    type: String,
    required: false
  },
  locationForecastDetailUrl: {
    type: String,
    required: false
  },
});

const mapStore = useMapStore();
const mapContainer = shallowRef(null);
const basemapChooserRef = ref();
let forecastData = ref([])
let map;

const alwaysOnTopLayers = [
  "admin-boundary-fill",
  "admin-boundary-line",
  "admin-boundary-line-1",
  "admin-boundary-line-lv-1",
  "weather-warnings",
  "weather-forecast"
];

const popupContent = ref(null);
const popupInstance = ref(null);

const popupVisible = ref(false);
const popupComponent = shallowRef(null);
const popupProps = ref({});


const activeTimeLayerDates = computed(() => {
  const activeLayerId = mapStore.activeTimeLayer;
  return activeLayerId ? mapStore.timeLayerDates[activeLayerId] || [] : [];
});

const selectedTimeLayerDateIndex = computed(() => {
  const activeLayerId = mapStore.activeTimeLayer;
  return activeLayerId ? mapStore.selectedTimeLayerDateIndex[activeLayerId] || 0 : 0;
});

const selectedDate = computed(() => {
  return activeTimeLayerDates.value[selectedTimeLayerDateIndex.value];
});


// Fetch map settings from API
const fetchMapSettings = async () => {
  const response = await fetch(props.mapSettingsUrl);
  return response.json();
};

// Initialize Map
const initializeMap = async () => {
  const mapInitOptions = {
    container: mapContainer.value,
    style: {
      version: 8,
      sources: {},
      layers: [],
    },
    center: [0, 0],
    zoom: 4,
    scrollZoom: false,
    attributionControl: false,
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

  // add attribution
  map.addControl(new maplibregl.AttributionControl({
    customAttribution: '<a href="https://maplibre.org" target="_blank">MapLibre</a>   &copy; <a href="http://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions" target="_blank">CARTO</a>',
    compact: false,
  }), "bottom-left");

  map.on("load", async () => {
    mapStore.setLoading(true);
    try {
      const mapSettings = await fetchMapSettings();
      mapStore.setLoading(false)
      initializeMapLayers(mapSettings);
    } catch (e) {
      console.log("Error fetching map settings", e)
      mapStore.setLoading(false)
    }
  });

  const interactiveLayers = ['weather-warnings', 'weather-forecast'];
  interactiveLayers.forEach(layer => {
    map.on('mouseenter', layer, () => {
      map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', layer, () => {
      map.getCanvas().style.cursor = '';
    });
  });

  map.on("click", (e) => {
    if (popupInstance.value) {
      popupInstance.value.remove();
      popupInstance.value = null;
    }

    const queryLayers = interactiveLayers.filter(l => mapStore.visibleLayers.find(layer => layer.id === l))

    const features = map.queryRenderedFeatures(e.point, {
      layers: queryLayers
    });

    // get first feature
    const feature = features && !!features.length && features[0];

    if (feature) {
      const layerId = feature.layer.id;

      if (layerId === "weather-warnings") {
        popupComponent.value = CAPWarningPopup;
        popupProps.value = {
          properties: feature.properties,
        };
      } else if (layerId === "weather-forecast") {
        popupComponent.value = LocationForecastPopup;

        popupProps.value = {
          properties: feature.properties,
          locationForecastDetailUrl: props.locationForecastDetailUrl,
        };
      }

      popupVisible.value = true;

      nextTick(() => {
        if (popupInstance.value) popupInstance.value.remove();


        popupInstance.value = new maplibregl.Popup()
            .setDOMContent(popupContent.value)
            .setLngLat(e.lngLat)
            .addTo(map);

        popupInstance.value.on("close", () => {
          popupVisible.value = false;
          popupInstance.value.remove();
          popupInstance.value = null;
        });
      });
    }
  });


};

const initializeMapLayers = async (mapSettings) => {
  const {
    boundaryTilesUrl,
    showWarningsLayer,
    capWarningsLayerDisplayName,
    capGeojsonUrl,
    showLocationForecastLayer,
    locationForecastLayerDisplayName,
    locationForecastDateDisplayFormat,
    homeForecastDataUrl,
    weatherIconsUrl,
    forecastClusterConfig,
    dynamicMapLayers,
    forecastSettingsUrl,
    zoomLocations,
    basemaps,
    showLevel1Boundaries
  } = mapSettings;

  if (basemaps && !!basemaps.length) {
    const defaultBasemap = basemaps.find(basemap => basemap.default) || basemaps[0]

    mapStore.setApiBaseMaps(basemaps);

    if (defaultBasemap) {
      const {mapStyle} = defaultBasemap
      const mapStyleJson = await fetch(mapStyle).then(res => res.json()).catch(e => console.error(e));

      if (mapStyleJson) {
        mapStyleJson.metadata = {
          ...mapStyleJson.metadata,
          customStyle: true,
        }
        map.setStyle(mapStyleJson)
        mapStore.setUsingApiStyle(true)
        mapStore.setSelectedApiBaseMap(defaultBasemap.id)

        setLabels()
      } else {
        map.setStyle(defaultMapStyle);
      }
    }
  } else {
    // if no basemaps are provided, set the default style
    map.setStyle(defaultMapStyle);
  }

  if (zoomLocations) {
    mapStore.setZoomLocations(zoomLocations)
    const defaultZoomLocation = zoomLocations.find(location => location.default)

    if (defaultZoomLocation) {
      mapStore.setSelectedZoomLocation(defaultZoomLocation.id)
    }
  }

  addBoundaryLayer(boundaryTilesUrl, showLevel1Boundaries);

  if (showWarningsLayer) {
    mapStore.updateLayerTitle("weather-warnings", capWarningsLayerDisplayName);
    addWarningsLayer(capGeojsonUrl);
  }

  if (showLocationForecastLayer) {
    mapStore.updateLayerTitle("weather-forecast", locationForecastLayerDisplayName);
    mapStore.updateLayerState("weather-forecast", true);
    mapStore.setWeatherForecastLayerDateFormat({currentTime: locationForecastDateDisplayFormat});

    try {
      const forecastSettings = await fetch(forecastSettingsUrl).then(res => res.json());
      mapStore.setForecastSettings(forecastSettings)
      addLocationForecastLayer(homeForecastDataUrl, weatherIconsUrl, forecastClusterConfig)

    } catch (e) {
      console.log("Error fetching forecast settings", e)
    }
  }

  if (dynamicMapLayers && !!dynamicMapLayers.length) {
    dynamicMapLayers.forEach(layer => {

      const dateFormat = layer.paramsSelectorConfig?.find(c => c.key === "time")?.dateFormat

      const mapStoreLayer = {
        ...layer,
        title: layer.display_name || layer.name,
        homeMapLayerType: "dynamic",
        "visible": false,
        "enabled": true,
        "icon": layer.icon ? `icon-${layer.icon}` : "icon-layers",
        dateFormat: dateFormat,
      }

      handleDynamicLayer(mapStoreLayer)
    })

    const defaultDynamicLayer = dynamicMapLayers.find(layer => layer.show_by_default)

    // if we have a default dynamic layer and warnings/locationForecast not enabled,
    // activate it
    if (defaultDynamicLayer && !showWarningsLayer && !showLocationForecastLayer) {
      toggleDynamicLayer(defaultDynamicLayer.id, true)
      mapStore.setActiveTimeLayer(defaultDynamicLayer.id)
      mapStore.updateLayerVisibility(defaultDynamicLayer.id, true)
    }
  }
};

const addBoundaryLayer = (boundaryTilesUrl, showLevel1Boundaries) => {
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
      'fill-color': "#fff",
      'fill-opacity': 0,
    },
    'metadata': {
      'mapbox:groups': 'boundary',
    }
  });


  map.addLayer({
    'id': 'admin-boundary-line',
    'type': 'line',
    'source': 'admin-boundary-source',
    "source-layer": "default",
    "filter": ["==", "level", 0],
    'paint': {
      "line-color": "#C0FF24",
      "line-width": 1,
      "line-offset": 1,
    },
    'metadata': {
      'mapbox:groups': 'boundary',
    }
  });


  map.addLayer({
    'id': 'admin-boundary-line-1',
    'type': 'line',
    'source': 'admin-boundary-source',
    "source-layer": "default",
    "filter": ["==", "level", 0],
    'paint': {
      "line-color": "#000",
      "line-width": 1.5,
    },
    'metadata': {
      'mapbox:groups': 'boundary',
    }
  });

  if (showLevel1Boundaries) {
    map.addLayer({
      'id': 'admin-boundary-line-lv-1',
      "type": "line",
      'source': 'admin-boundary-source',
      "source-layer": "default",
      "filter": ["==", "level", 1],
      "paint": {
        "line-color": "#8b8b8b",
        "line-width": 0.8,
        "line-dasharray": [2, 4],
      },
      'metadata': {
        'mapbox:groups': 'boundary',
      }
    });
  }
}

const addWarningsLayer = (capGeojsonUrl) => {
  fetch(capGeojsonUrl).then(res => res.json()).then(alertsGeojson => {
    if (alertsGeojson.features.length > 0) {
      mapStore.updateLayerState("weather-warnings", true);

      const bounds = turfBbox(alertsGeojson);

      // fit map to alert bounds
      map.fitBounds(bounds, {padding: 50});

      // add cap alerts layer
      map.addSource("weather-warnings", {
        type: "geojson",
        data: alertsGeojson,
      });


      let beforeLayer

      if (map.getLayer("weather-forecast")) {
        beforeLayer = "weather-forecast"
      }

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
      }, beforeLayer);

      mapStore.updateLayerVisibility("weather-warnings", true);
    }
  })
}


const addLocationForecastLayer = (homeForecastDataUrl, weatherIconsUrl, forecastClusterConfig) => {
  // add city forecast source
  map.addSource("weather-forecast", {
    type: "geojson",
    data: {type: "FeatureCollection", features: []},
    ...forecastClusterConfig,
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

  mapStore.setLoading(true)

  fetch(homeForecastDataUrl).then(res => res.json()).then(response => {
    // get and set weather icons
    addWeatherIcons(weatherIconsUrl)
    // set city forecast data
    setCityForecastData(response)

    const {data} = response

    if (data && !!data.length) {
      mapStore.updateLayerVisibility("weather-forecast", true)
    }

    mapStore.setLoading(false)

    setLabels()

  }).catch(e => {
    mapStore.setLoading(false)
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
  mapStore.setSelectedTimeLayerDateIndex("weather-forecast", 0)
  mapStore.setTimeLayerDates("weather-forecast", dates)
}

const updateMapCityForecastData = (date) => {
  const selectedDateData = forecastData.value.find(d => d.datetime === date)
  if (selectedDateData) {
    map.getSource("weather-forecast").setData(selectedDateData)
  }
}

const handleDynamicLayer = (layer) => {
  const {layerType} = layer

  if (layerType === "raster_file") {
    layer.mapLayerConfig = getRasterLayerConfig(layer)
    mapStore.addLayer(layer)
  } else if (layerType === "wms") {
    const {getCapabilitiesUrl, getCapabilitiesLayerName} = layer
    // valid WMS layer must have getCapabilitiesUrl and getCapabilitiesLayerName
    if (getCapabilitiesUrl && getCapabilitiesLayerName) {
      layer.mapLayerConfig = getRasterLayerConfig(layer)
      mapStore.addLayer(layer)
    }
  } else if (layerType === "vector_tile") {
    layer.mapLayerConfig = getVectorTileLayerConfig(layer)
    mapStore.addLayer(layer)
  } else {
    console.error("Unsupported layer type:", layerType);
  }
}

const toggleDynamicLayer = (layerId, visible) => {
  const layer = mapStore.getLayerById(layerId)
  const {layerType} = layer

  if (!visible) {
    if (layerType === "vector_tile") {
      const {layers} = layer.mapLayerConfig
      layers && layers.forEach(layer => {
        if (map.getLayer(layer.id)) {
          map.removeLayer(layer.id)
        }
      })
    } else {
      if (map.getLayer(layerId)) {
        map.removeLayer(layerId)
      }
    }

    if (map.getSource(layerId)) {
      map.removeSource(layerId)
    }


  } else {
    if (layerType === "raster_file" || layerType === "wms" || layerType === "vector_tile") {
      addDynamicLayer(layer.id)
    }
  }
}

const getTimeValuesFromTileJson = (tileJsonUrl, timestampsResponseObjectKey = "timestamps") => {
  return fetch(tileJsonUrl).then(res => res.json()).then(res => {
    return res[timestampsResponseObjectKey]
  })
}

const fetchTimestamps = (layer) => {
  const {layerType} = layer

  if (layerType === "raster_file" || layerType === "vector_tile") {
    const {tileJsonUrl, timestampsResponseObjectKey} = layer
    return getTimeValuesFromTileJson(tileJsonUrl, timestampsResponseObjectKey)
  } else if (layerType === "wms") {
    const {getCapabilitiesUrl, getCapabilitiesLayerName} = layer
    return getTimeValuesFromWMS(getCapabilitiesUrl, getCapabilitiesLayerName)
  } else {
    console.error("Unsupported layer type:", layerType);
  }

  return []
}

const addDynamicLayer = async (layerId) => {
  const layer = mapStore.getLayerById(layerId)
  const {mapLayerConfig, layerType, paramsSelectorConfig} = layer
  const {currentTimeMethod} = layer

  try {
    mapStore.setLoading(true)

    const timestamps = await fetchTimestamps(layer)
    const sortedTimestamps = timestamps.sort((a, b) => new Date(a) - new Date(b));

    if (sortedTimestamps && !!sortedTimestamps.length) {
      const currentLayerTime = getTimeFromList([...sortedTimestamps], currentTimeMethod);
      const currentLayerTimeIndex = sortedTimestamps.indexOf(currentLayerTime);

      mapStore.setSelectedTimeLayerDateIndex(layer.id, currentLayerTimeIndex)
      mapStore.setTimeLayerDates(layer.id, timestamps)

      const sourceId = mapLayerConfig.source.id

      let tileUrl
      const timeSelectorConfig = paramsSelectorConfig.find(c => c.key === "time")

      if (timeSelectorConfig) {
        let timeUrlParam = "time"
        const {url_param} = timeSelectorConfig
        if (url_param) {
          timeUrlParam = url_param
        }
        tileUrl = updateTileUrl(mapLayerConfig.source.tiles[0], {[timeUrlParam]: currentLayerTime})
      }

      if (tileUrl) {
        if (!map.getSource(sourceId)) {
          map.addSource(sourceId, {
            ...mapLayerConfig.source,
            tiles: [tileUrl],
          });
        }

        if (layerType === "raster_file" || layerType === "wms") {
          if (!map.getLayer(layerId)) {
            map.addLayer({
              id: layerId,
              type: "raster",
              source: sourceId,
            });
          }
        } else if (layerType === "vector_tile") {
          const {layers} = mapLayerConfig
          layers && layers.forEach(layer => {
            if (!map.getLayer(layer.id)) {
              map.addLayer({
                ...layer,
                source: sourceId,
              });
            }
          })
        }

        // move always on top layers to the top
        alwaysOnTopLayers.forEach(l => {
          if (map.getLayer(l)) {
            map.moveLayer(l)
          }
        });

        setLabels()
      }
    }

    mapStore.setLoading(false)
  } catch (e) {
    console.log("Error adding dynamic layer", e)
    mapStore.setLoading(false)
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

  const {homeMapLayerType} = layer

  // turn on/off fixed layer
  if (homeMapLayerType === "fixed" && map.getLayer(layerId)) {
    map.setLayoutProperty(layerId, "visibility", visible ? "visible" : "none");
  }

  // handle time layers
  if (layer.multiTemporal) {
    if (visible) {
      // if we have an active time layer, switch it off
      if (mapStore.activeTimeLayer) {
        mapStore.updateLayerVisibility(mapStore.activeTimeLayer, false)

        if (map.getLayer(mapStore.activeTimeLayer)) {
          map.setLayoutProperty(mapStore.activeTimeLayer, "visibility", "none");
        }

        // remove source and layer from map
        if (mapStore.activeTimeLayer !== "weather-forecast") {
          toggleDynamicLayer(mapStore.activeTimeLayer, false)
        }
      }
      mapStore.setActiveTimeLayer(layerId)
    } else {
      mapStore.setActiveTimeLayer(null)
    }
  }

  if (homeMapLayerType === "dynamic") {
    toggleDynamicLayer(layerId, visible)
  }
};

const handleDynamicLayerTimeChange = (layer, newDateStr) => {
  const {layerType, mapLayerConfig, paramsSelectorConfig} = layer

  if (layerType === "raster_file" || layerType === "wms" || layerType === "vector_tile") {
    const timeSelectorConfig = paramsSelectorConfig.find(c => c.key === "time")
    let timeUrlParam = "time"
    if (timeSelectorConfig) {
      const {url_param} = timeSelectorConfig
      if (url_param) {
        timeUrlParam = url_param
      }
    }

    if (mapLayerConfig) {
      updateSourceTileUrl(map, mapLayerConfig.source.id, {[timeUrlParam]: newDateStr})
    }
  }
}

const setAPIBaseMap = (basemapId) => {
  const basemap = mapStore.getApiBaseMapById(basemapId)
  const BASEMAP_GROUPS = ["basemap"];

  if (map) {
    const {layers, metadata} = map.getStyle();
    const basemapGroups = Object.keys(metadata["mapbox:groups"]).filter(
        (k) => {
          const {name} = metadata["mapbox:groups"][k];
          const matchedGroups = BASEMAP_GROUPS.map((rgr) =>
              name?.toLowerCase()?.includes(rgr)
          );

          return matchedGroups.some((bool) => bool);
        }
    );

    const basemapsWithMeta = basemapGroups.map((_groupId) => ({
      ...metadata["mapbox:groups"][_groupId],
      id: _groupId,
    }));

    const basemapToDisplay = basemapsWithMeta.find((_basemap) =>
        _basemap.name.includes(basemap.basemapGroup)
    );

    if (basemapToDisplay) {
      const basemapLayers = layers.filter((l) => {
        const {metadata: layerMetadata} = l;
        if (!layerMetadata) return false;
        const gr = layerMetadata["mapbox:group"];
        return basemapGroups.includes(gr);
      });

      basemapLayers.forEach((_layer) => {
        const match = _layer.metadata["mapbox:group"] === basemapToDisplay.id;

        if (!match) {
          map.setLayoutProperty(_layer.id, "visibility", "none");
        } else {
          map.setLayoutProperty(_layer.id, "visibility", "visible");
        }
      });
    }
  }
}

const setLabels = () => {
  const usingApiStyle = mapStore.usingApiStyle

  if (!usingApiStyle) return

  const basemap = mapStore.getSelectedApiBaseMap()
  const showMapLabels = true
  const labelsLang = "en"

  const LABELS_GROUP = ["labels"];

  if (map && map.getStyle()) {
    const {layers, metadata} = map.getStyle();

    const labelGroups = Object.keys(metadata["mapbox:groups"]).filter((k) => {
      const {name} = metadata["mapbox:groups"][k];

      const matchedGroups = LABELS_GROUP.filter((rgr) =>
          name.toLowerCase().includes(rgr)
      );

      return matchedGroups.some((bool) => bool);
    });

    const labelsWithMeta = labelGroups.map((_groupId) => ({
      ...metadata["mapbox:groups"][_groupId],
      id: _groupId,
    }));
    const labelsToDisplay =
        labelsWithMeta.find((_basemap) =>
            _basemap.name.includes(basemap?.labelsGroup)
        ) || {};

    const labelLayers = layers.filter((l) => {
      const {metadata: layerMetadata} = l;
      if (!layerMetadata) return false;

      const gr = layerMetadata["mapbox:group"];
      return labelGroups.includes(gr);
    });

    labelLayers.forEach((_layer) => {
      const match = _layer.metadata["mapbox:group"] === labelsToDisplay.id;
      map.setLayoutProperty(
          _layer.id,
          "visibility",
          match && showMapLabels ? "visible" : "none"
      );
      map.setLayoutProperty(_layer.id, "text-field", ["get", `name_${labelsLang}`]);

      map.moveLayer(_layer.id);
    });
  }


}

watch(() => mapStore.selectedApiBaseMap, (newSelectedApiBaseMapId) => {
  setAPIBaseMap(newSelectedApiBaseMapId);
});


watch(selectedDate, (newSelectedDate) => {
  const activeLayerId = mapStore.activeTimeLayer;

  if (activeLayerId) {
    const layer = mapStore.getLayerById(activeLayerId)
    const {homeMapLayerType} = layer


    if (homeMapLayerType === "fixed") {
      if (activeLayerId === "weather-forecast") {
        updateMapCityForecastData(newSelectedDate)
      }
    } else {
      handleDynamicLayerTimeChange(layer, newSelectedDate)
    }
  }
});

watch(() => mapStore.selectedBasemap, (newBasemap) => {
  const mapStyle = map.getStyle()
  const backgroundLayers = mapStyle.layers.filter(layer => layer.metadata && layer.metadata["mapbox:groups"] === "background")

  backgroundLayers.forEach(layer => {
    if (layer.id === newBasemap) {
      map.setLayoutProperty(layer.id, 'visibility', 'visible')
    } else {
      map.setLayoutProperty(layer.id, 'visibility', 'none')
    }
  })
});


watch(() => mapStore.showBoundary, (newShowBoundary) => {
  const mapStyle = map.getStyle()
  const backgroundLayers = mapStyle.layers.filter(layer => layer.metadata && layer.metadata["mapbox:groups"] === "boundary")

  backgroundLayers.forEach(layer => {
    if (newShowBoundary) {
      map.setLayoutProperty(layer.id, 'visibility', 'visible')
    } else {
      map.setLayoutProperty(layer.id, 'visibility', 'none')
    }
  })
});

watch(() => mapStore.selectedZoomLocation, (newSelectedZoomLocationId) => {
  const zoomLocation = mapStore.zoomLocations.find(location => location.id === newSelectedZoomLocationId)
  if (zoomLocation && zoomLocation.bounds) {
    const bounds = zoomLocation.bounds
    map.fitBounds([[bounds[0], bounds[1]], [bounds[2], bounds[3]]], {padding: 50});
  }
});

onMounted(() => initializeMap());
onUnmounted(() => map?.remove());
</script>


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
      <MapOptions/>
    </Popover>
  </div>

  <!-- DatePicker for screens < desktop size -->
  <div id="datepicker-mobile"></div>

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

  <div class="dynamic-layer-control">
    <LayerItem
        v-for="layer in mapStore.sortedDynamicLayers"
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

  <div class="legend-control">
    <Legend/>
  </div>

  <!-- Overlay Loader -->
  <div v-if="mapStore.loading" class="overlay-loader">
    <div class="spinner"></div>
  </div>

  <teleport to="body" v-if="popupVisible">
    <div ref="popupContent">
      <component
          :is="popupComponent"
          v-bind="popupProps"
      />
    </div>
  </teleport>

</template>

<style>
.maplibregl-popup-content {
  box-shadow: 0 3px 14px rgba(0, 0, 0, 0.4);
}
</style>

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
  display: flex;
  justify-content: center;
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

#datepicker-mobile {
  position: absolute;
  top: 130px;
  right: 10px;
}

.fixed-layer-control {
  position: absolute;
  top: 20px;
  left: 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dynamic-layer-control {
  position: absolute;
  bottom: 30px;
  left: 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.date-navigator-control {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px;
}

.legend-control {
  position: absolute;
  bottom: 12px;
  right: 10px;
}


.overlay-loader {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, .7);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-top: 4px solid #000; /* Spinner color */
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0);
  }
  100% {
    transform: rotate(360deg);
  }
}


</style>