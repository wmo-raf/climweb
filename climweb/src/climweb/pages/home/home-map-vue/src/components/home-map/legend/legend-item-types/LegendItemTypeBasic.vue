<script setup>
import {computed} from "vue";

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
  return props.legendConfig && props.legendConfig.type === 'basic' && props.legendConfig.items && props.legendConfig.items.length > 0;
})

</script>

<template>
  <div v-if="enabled" class="m-legend-item">
    <div class="legend-title">{{ props.title }}</div>
    <ul>
      <li v-for="item in props.legendConfig.items" class="item-wrapper">
        <div class="item-color" :style="{ backgroundColor: item.color }"></div>
        <div class="item-label">{{ item.name }}</div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.m-legend-item {
  display: flex;
  flex-direction: column;
}

.legend-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
}

.legend-item-type-basic ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item-wrapper {
  display: flex;
  align-items: center;
}

.item-color {
  height: 12px;
  width: 12px;
  border-radius: 50%;
  margin-right: 4px;
}

.item-label {
  font-size: 12px;
  color: #000;
  font-weight: 400;
  line-height: 1.5;
  margin: 0;
  padding: 0;
  display: flex;
  align-items: center;
  gap: 4px;
}


</style>