<script setup>

import {ref, watch} from "vue";

const props = defineProps({
  id: {
    type: String,
    required: true
  },
  layerType: {
    type: String,
    required: true
  },
  position: {
    type: Number,
    required: true
  },
  title: {
    type: String,
    required: true
  },
  icon: {
    type: String,
    required: false
  },
  active: {
    type: Boolean,
    required: false,
    default: false
  }
});

const emit = defineEmits(['update:toggleLayer']);
const isActive = ref(props.active);

watch(
    () => props.active,
    (newActiveValue) => {
      isActive.value = newActiveValue;
    }
);

const onToggle = () => {
  isActive.value = !isActive.value;
  emit('update:toggleLayer', {layerId: props.id, active: isActive.value});
};

</script>

<template>
  <div class="layer-control" :class="{ active: isActive }" @click="onToggle">
    <div class="layer-icon">
      <svg>
        <use xlink:href="#icon-layers"></use>
      </svg>
    </div>
    <div class="layer-title">
      {{ title }}
    </div>
  </div>
</template>

<style scoped>


.layer-control {
  position: relative;
  display: flex;
  background: rgba(0, 0, 0, .5);
  border-top-right-radius: 20px;
  border-bottom-right-radius: 20px;
  font-weight: 700;
  color: #fff;
  padding: 0 12px;
  align-items: center;
  height: 30px;
  width: fit-content;
  max-width: 100%;
  white-space: nowrap;
  cursor: pointer;
}

.layer-control.active {
  background-color: var(--primary-color);
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
}

.layer-title {
  padding-left: 12px;
}
</style>