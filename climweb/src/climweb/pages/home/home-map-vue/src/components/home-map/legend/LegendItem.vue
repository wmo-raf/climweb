<script setup>
import LegendItemTypeBasic from "./legend-item-types/LegendItemTypeBasic.vue"
import LegendItemTypeChoroplethHorizontal from "./legend-item-types/LegendItemTypeChoroplethHorizontal.vue";
import LegendItemTypeChoroplethVertical from "./legend-item-types/LegendItemTypeChoroplethVertical.vue";
import LegendItemTypeGradientHorizontal from "./legend-item-types/LegendItemTypeGradientHorizontal.vue";
import LegendItemTypeGradientVertical from "./legend-item-types/LegendItemTypeGradientVertical.vue";

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

</script>

<template>
  <LegendItemTypeBasic :legend-config="props.legendConfig" :title="props.title"/>
  <LegendItemTypeChoroplethHorizontal :legend-config="props.legendConfig" :title="props.title"/>
  <LegendItemTypeChoroplethVertical :legend-config="props.legendConfig" :title="props.title"/>
  <LegendItemTypeGradientHorizontal :legend-config="props.legendConfig" :title="props.title"/>
  <LegendItemTypeGradientVertical :legend-config="props.legendConfig" :title="props.title"/>
</template>
<style scoped>
</style>