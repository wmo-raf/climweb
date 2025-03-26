<script setup>
import {computed} from 'vue';
import {useMapStore} from "@/stores/map";
import {dFormatter} from "@/utils";

const mapStore = useMapStore();

const activeTimeLayerDates = computed(() => {
  const activeLayerId = mapStore.activeTimeLayer;
  return activeLayerId ? mapStore.timeLayerDates[activeLayerId] || [] : [];
});


const dateDisplayFormat = computed(() => {
  const activeLayerId = mapStore.activeTimeLayer;
  const layer = activeLayerId && mapStore.getLayerById(activeLayerId);
  return layer && layer.dateFormat ? layer.dateFormat : {currentTime: "yyyy-MM-dd HH:mm"}
});

const selectedTimeLayerDateIndex = computed(() => {
  const activeLayerId = mapStore.activeTimeLayer;
  return activeLayerId ? mapStore.selectedTimeLayerDateIndex[activeLayerId] || 0 : 0;
});

const selectedDate = computed(() => {
  return activeTimeLayerDates.value[selectedTimeLayerDateIndex.value];
});

const selectedDateFormatted = computed(() => {
  if (selectedDate.value && dateDisplayFormat.value) {
    const {currentTime, asPeriod} = dateDisplayFormat.value
    return dFormatter(new Date(selectedDate.value), currentTime, asPeriod);
  }
  return "";
});

const nextDisabled = computed(() => selectedTimeLayerDateIndex.value >= activeTimeLayerDates.value.length - 1);
const prevDisabled = computed(() => selectedTimeLayerDateIndex.value <= 0);

const selectNext = () => {
  if (!nextDisabled.value) {
    const nextIndex = selectedTimeLayerDateIndex.value + 1;
    mapStore.setSelectedTimeLayerDateIndex(mapStore.activeTimeLayer, nextIndex);
  }
};

const selectPrev = () => {
  if (!prevDisabled.value) {
    const prevIndex = selectedTimeLayerDateIndex.value - 1;
    mapStore.setSelectedTimeLayerDateIndex(mapStore.activeTimeLayer, prevIndex);
  }
};


</script>

<template>
  <div class="time-picker" v-if="!!activeTimeLayerDates.length">
    <button @click="selectPrev" :disabled="prevDisabled" class="nav-button">◄</button>
    <span class="date-display">{{ selectedDateFormatted }}</span>
    <button @click="selectNext" :disabled="nextDisabled" class="nav-button">►</button>
  </div>
</template>

<style scoped>
.time-picker {
  display: flex;
  align-items: center;
  background: rgba(0, 0, 0, .6);
  color: white;
  border-radius: 5px;
  font-family: Arial, sans-serif;
  font-size: 16px;
}

.nav-button {
  background: none;
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
  padding: 5px;
}

.nav-button:disabled {
  color: gray;
  cursor: not-allowed;
}

.date-display {
  margin: 0 10px;
  font-weight: bold;
}
</style>