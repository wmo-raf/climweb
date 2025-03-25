<script setup>
import {computed, ref, watch} from 'vue';
import {useMapStore} from "@/stores/map";
import {format as formatDate} from "date-fns"

const mapStore = useMapStore();

const selectedIndex = ref(0);

const activeTimeLayerDates = computed(() => {
  const activeLayerId = mapStore.activeTimeLayer;
  return activeLayerId ? mapStore.timeLayerDates[activeLayerId]?.value || [] : [];
});

const dateDisplayFormat = computed(() => {
  const activeLayerId = mapStore.activeTimeLayer;
  const layer = activeLayerId && mapStore.getLayerById(activeLayerId);

  return layer ? layer.dateFormat : "yyyy-MM-dd HH:mm"
});

console.log(dateDisplayFormat)


const selectedDate = computed(() => activeTimeLayerDates.value[selectedIndex.value] || '');
const selectedDateFormatted = computed(() => {
  return formatDate(new Date(selectedDate.value), dateDisplayFormat.value);
});

const nextDisabled = computed(() => selectedIndex.value >= activeTimeLayerDates.value.length - 1);
const prevDisabled = computed(() => selectedIndex.value <= 0);

const selectNext = () => {
  if (!nextDisabled.value) {
    selectedIndex.value++;
    mapStore.setSelectedTimeLayerDate(mapStore.activeTimeLayer, selectedDate.value);
  }
};

const selectPrev = () => {
  if (!prevDisabled.value) {
    selectedIndex.value--;
    mapStore.setSelectedTimeLayerDate(mapStore.activeTimeLayer, selectedDate.value);
  }
};

watch(activeTimeLayerDates, (newDates) => {
  if (!newDates.length) {
    // Reset index and do not update selectedDate if no valid dates
    selectedIndex.value = 0;
  } else {
    selectedIndex.value = 0;
    mapStore.setSelectedTimeLayerDate(mapStore.activeTimeLayer, selectedDate.value);
  }
});

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