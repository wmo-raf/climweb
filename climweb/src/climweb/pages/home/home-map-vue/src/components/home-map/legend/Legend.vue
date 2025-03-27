<script setup>

import {useMapStore} from "@/stores/map";
import LegendItem from "./LegendItem.vue";

const mapStore = useMapStore();

</script>

<template>
  <div class="hm-legend">
    <div v-for="layer in mapStore.visibleLayers">
      <LegendItem :legend-config="layer.legendConfig" :title="layer.title"/>
    </div>
  </div>
</template>

<style>

.hm-legend {
  z-index: 1000;
  background-color: white;
  border-radius: 5px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  min-width: 150px;
}

.m-legend-item {
  padding: 10px;
  border-bottom: 1px solid #f0f0f0;
}

</style>