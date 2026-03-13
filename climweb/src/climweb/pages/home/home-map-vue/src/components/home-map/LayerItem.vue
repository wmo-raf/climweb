<script setup>
import { ref, watch, computed } from "vue";
import { useMapStore } from "@/stores/map";
import DateNavigator from "./DateNavigator.vue";

const props = defineProps({
  id: { type: String, required: true },
  homeMapLayerType: { type: String, required: true },
  position: { type: Number, required: true },
  title: { type: String, required: true },
  icon: { type: String, required: false },
  enabled: { type: Boolean, default: false },
  visible: { type: Boolean, default: false },
  multiTemporal: { type: Boolean, default: false }
});

const emit = defineEmits([
  "update:toggleLayer",
  "update:timeChange",
  "update:opacity"
]);

const onOpacityChange = (event) => {
  emit("update:opacity", {
    layerId: props.id,
    opacity: parseFloat(event.target.value)
  });
};


const mapStore = useMapStore();

const isVisible = ref(props.visible);
const isEnabled = ref(props.enabled);

watch(() => props.visible, val => isVisible.value = val);
watch(() => props.enabled, val => isEnabled.value = val);

const dates = computed(() =>
  mapStore.timeLayerDates[props.id] || []
);

const selectedIndex = computed(() =>
  mapStore.selectedTimeLayerDateIndex[props.id] || 0
);

const onToggle = () => {
  isVisible.value = !isVisible.value;
  emit("update:toggleLayer", {
    layerId: props.id,
    visible: isVisible.value
  });
};

const handleTimeChange = (newDate) => {
  emit("update:timeChange", {
    layerId: props.id,
    newDate
  });
};
</script>


<template>
  <div v-if="isEnabled" class="layer-wrapper">

    <!-- Toggle -->
    <div
      class="layer-control"
      :class="{ active: isVisible }"
      @click="onToggle"
    >
      <div class="layer-icon">
        <svg>
          <use :xlink:href="icon ? `#${icon}` : '#icon-layers'"></use>
        </svg>
      </div>

      <div class="layer-title">
        {{ title }}
      </div>
    </div>

    <!-- Date Navigator -->
    <DateNavigator
      v-if="multiTemporal && isVisible && dates.length"
      :layerId="id"
      :dates="dates"
      :selectedIndex="selectedIndex"
      :dateFormat="mapStore.getLayerById(id)?.dateFormat"
      @change="handleTimeChange"
    />

    <input
      v-if="homeMapLayerType === 'dynamic' && isVisible"
      type="range"
      min="0"
      max="1"
      step="0.05"
      :value="mapStore.getLayerById(id)?.opacity ?? 1"
      @input="onOpacityChange"
      class="opacity-slider"
    />



  </div>
</template>


<style scoped>


.layer-control {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: rgba(0, 0, 0, .3);
  border-top-right-radius: 20px;
  border-bottom-right-radius: 20px;
  font-weight: 700;
  color: #fff;
  padding: 0 12px;
  height: 30px;
  width: fit-content;
  max-width: 100%;
  white-space: nowrap;
  cursor: pointer;
}

.layer-control.active {
  background-color: var(--primary-color);
}

.layer-control.mobile {
  padding: 0;
}

.layer-icon {
  background: #fff;
  border-radius: 2em;
  width: 32px;
  height: 32px;
  position: absolute;
  left: -15px;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 2px 3px rgba(0, 0, 0, .25);
}

.layer-icon svg {
  height: 18px;
  width: 18px;
  fill: var(--primary-color);
  color: var(--primary-color);
}

.layer-title {
  padding-left: 12px;
}

.layer-wrapper {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.opacity-slider {
  width: 100%;
    accent-color: var(--primary-color);
    height: 4px;

}


</style>