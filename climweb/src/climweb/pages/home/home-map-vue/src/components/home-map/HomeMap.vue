<template>
  <Map :initialBounds :mapSettingsUrl :locationForecastDetailUrl/>
</template>

<script setup>
import Map from "./Map.vue";

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
  languageCode: {
    type: String,
    required: false,
    default: 'en'
  }
});

</script>

<style>
/* Add global styles if needed */
</style>