<script setup>
import { computed } from "vue";
import { breakpointsTailwind, useBreakpoints } from "@vueuse/core";
import { dFormatter } from "@/utils/date";

const props = defineProps({
  layerId: { type: String, required: true },
  dates: { type: Array, required: true },
  selectedIndex: { type: Number, required: true },
  dateFormat: { type: Object, default: () => ({ currentTime: "yyyy-MM-dd HH:mm" }) }
});

const emit = defineEmits(["change"]);

const selectedDate = computed(() =>
  props.dates[props.selectedIndex]
);

const selectedDateFormatted = computed(() => {
  if (!selectedDate.value) return "";
  const { currentTime, asPeriod } = props.dateFormat;
  return dFormatter(new Date(selectedDate.value), currentTime, asPeriod);
});

const nextDisabled = computed(() =>
  props.selectedIndex >= props.dates.length - 1
);

const prevDisabled = computed(() =>
  props.selectedIndex <= 0
);

const selectNext = () => {
  if (!nextDisabled.value) {
    emit("change", props.dates[props.selectedIndex + 1]);
  }
};

const selectPrev = () => {
  if (!prevDisabled.value) {
    emit("change", props.dates[props.selectedIndex - 1]);
  }
};

const breakpoints = useBreakpoints(breakpointsTailwind);
const isDesktop = breakpoints.greater("md");
</script>

<template>
  <Teleport to="#datepicker-mobile" :disabled="isDesktop">
    <div class="time-picker" v-if="dates.length">
      <button @click="selectPrev" :disabled="prevDisabled" class="nav-button">◄</button>
      <span class="date-display">{{ selectedDateFormatted }}</span>
      <button @click="selectNext" :disabled="nextDisabled" class="nav-button">►</button>
    </div>
  </Teleport>
</template>


<style scoped>

.time-picker {
    display: flex;
    align-items: center;
    background: #f5f5f5;
    color: var(--primary-color);
    border-radius: 20px;
    font-family: Arial, sans-serif;
    border: solid 0.05rem var(--primary-color);
    font-size: 12px;
  }

.nav-button {
  background: none;
  border: none;
  color: var(--primary-color);
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