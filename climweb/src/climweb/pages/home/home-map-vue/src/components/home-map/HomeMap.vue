<template>
  <Map :initialBounds :mapSettingsUrl/>
</template>

<script setup>
import Map from "./Map.vue";

const props = defineProps({
  mapSettingsUrl: {
    type: String,
    required: true
  },
  cityDetailUrl: {
    type: String,
    required: false
  },
  initialBounds: {
    type: String,
    required: false
  }
});

</script>

<style>
/* Add global styles if needed */
</style>