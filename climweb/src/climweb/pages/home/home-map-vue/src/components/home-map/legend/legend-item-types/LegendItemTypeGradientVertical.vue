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
  return props.legendConfig && props.legendConfig.type === 'gradient_vertical' && props.legendConfig.items && props.legendConfig.items.length > 0;
})

const items = computed(() => {
  return enabled.value ? props.legendConfig.items.filter(item => item.color !== "transparent") : []
})

const itemTransparent = computed(() => {
  return enabled.value ? props.legendConfig.items.find(item => item.color === "transparent") : null;
})

const gradient = computed(() => {
  return enabled.value ? props.legendConfig.items.map(item => item.color).join(",") : "";
})


const itemTransparentWidth = computed(() => {
  return itemTransparent.value ? (1 / props.legendConfig.items.length) * 100 : 0;
})

const gradientHeight = computed(() => {
  return items.value.length ? `${(items.value.length * 24)}px` : 0;
})

const gradientStyle = computed(() => {
  return enabled ? `linear-gradient(to bottom, ${gradient.value})` : "";
})

</script>

<template>
  <div v-if="enabled" class="m-legend-item">
    <div class="legend-title">{{ props.title }}</div>

    <div class="legend-gradient-icon">
      <div v-if="itemTransparent" class="icon-gradient-transparent" :style="{width:12,height:24}"></div>
      <div class="icon-gradient" :style="{height:gradientHeight, backgroundImage:gradientStyle}"></div>
      <ul>
        <li v-for="item in items" :key="item.value">
          <span class="name">{{ item.name || item.value }}</span>
        </li>
      </ul>
    </div>

  </div>
</template>

<style scoped>

.legend-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
}

.legend-gradient-icon {
  display: flex;
}

.icon-gradient {
  display: block;
  width: 12px;
}

.icon-gradient-transparent {
  display: block;
  height: 5px;
  width: 12px;
  margin-bottom: 5px;
  background-image: linear-gradient(
      45deg,
      rgba(black, 0.4) 25%,
      transparent 25%,
      transparent 75%,
      rgba(black, 0.4) 75%,
      rgba(black, 0.4)
  ),
  linear-gradient(
      45deg,
      rgba(black, 0.4) 25%,
      transparent 25%,
      transparent 75%,
      rgba(black, 0.4) 75%,
      rgba(black, 0.4)
  );

  background-size: 4px 4px;
  background-position: 0 0, 2px 2px;
}

ul {
  display: flex;
  flex-direction: column;
  margin: 0 0 0 8px;
  padding: 0;
  list-style: none;
  font-size: 12px;
}

li {
  padding: 0;
  margin: 0;
  flex: 1 1 auto;
  height: 24px;
}

li &:before {
  content: none !important;
}

li .name {
  font-size: 12px;
  display: block;
  font-family: inherit;
}


</style>