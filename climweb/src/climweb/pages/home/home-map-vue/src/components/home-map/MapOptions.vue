<script setup>
import RadioButton from 'primevue/radiobutton';
import Checkbox from 'primevue/checkbox';
import {useMapStore} from "@/stores/map";

const mapStore = useMapStore();

</script>

<template>
  <div class="map-options">
    <div class="basemap-options">
      <div v-for="basemap in mapStore.basemaps" :key="basemap.value" class="basemap-item">
        <RadioButton v-model="mapStore.selectedBasemap" :inputId="basemap.value" name="basemap" :value="basemap.value"
                     class="basemap-input"/>
        <label :for="basemap.value">{{ basemap.label }}</label>
      </div>
    </div>
    <div class="divisor"></div>
    <div class="boundary-check">
      <Checkbox v-model="mapStore.showBoundary" inputId="boundary" name="boundary" value="yes" binary/>
      <label for="boundary"> Boundaries </label>
    </div>
  </div>


</template>

<style scoped>

.map-options {
  font-size: 14px;
}


.basemap-options {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.divisor {
  width: 100%;
  height: 1px;
  border-top: 1px solid rgba(26, 28, 34, .1);
  margin: 15px 0;
}

.basemap-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

</style>

<style>
.p-checkbox-checked .p-checkbox-box, .p-radiobutton-checked .p-radiobutton-box {
  border-color: var(--primary-color);
  background: var(--primary-color);
}


</style>