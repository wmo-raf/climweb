<script setup>
import {computed} from "vue";
import {createLegend} from "@/utils/legend.js";

const props = defineProps({
  legendConfig: {
    type: Object,
    required: false,
  },
  title: {
    type: String,
    required: false,
  }
})

const enabled = computed(() => {
  return props.legendConfig && props.legendConfig.type === 'choropleth' && props.legendConfig.items && props.legendConfig.items.length > 0;
})

const computedLegend = computed(() => {
  return enabled ? createLegend(props.legendConfig) : null
})


</script>

<template>
  <div v-if="enabled" class="m-legend-item">
    <div class="legend-title">{{ props.title }}</div>
    <div v-html="computedLegend.outerHTML"></div>
  </div>
</template>

<style scoped>
.legend-title {
  font-size: 13px;
  font-weight: 600;
}
</style>