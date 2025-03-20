<script setup>
import {ref, computed} from 'vue';

const props = defineProps({
  dates: {
    type: Array,
    required: true,
  },
});

const emit = defineEmits(['update:selectedDate']);

const selectedIndex = ref(0);

const selectedDate = computed(() => props.dates[selectedIndex.value] || '');

const nextDisabled = computed(() => selectedIndex.value >= props.dates.length - 1);
const prevDisabled = computed(() => selectedIndex.value <= 0);

const selectNext = () => {
  if (!nextDisabled.value) {
    selectedIndex.value++;
    emit('update:selectedDate', selectedDate.value);
  }
};

const selectPrev = () => {
  if (!prevDisabled.value) {
    selectedIndex.value--;
    emit('update:selectedDate', selectedDate.value);
  }
};

defineExpose({
  getSelectedDate: () => selectedDate.value,
});
</script>

<template>
  <div class="time-picker">
    <button @click="selectPrev" :disabled="prevDisabled" class="nav-button">◄</button>
    <span class="date-display">{{ selectedDate }}</span>
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
