<script setup>

import {ref, watch} from "vue";


const props = defineProps({
  id: {
    type: String,
    required: true
  },
  homeMapLayerType: {
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
  enabled: {
    type: Boolean,
    required: false,
    default: false
  },
  visible: {
    type: Boolean,
    required: false,
    default: false
  },
  multiTemporal: {
    type: Boolean,
    required: false,
    default: false
  }
});

const emit = defineEmits(['update:toggleLayer']);
const isVisible = ref(props.visible);
const isEnabled = ref(props.enabled);


watch(
    () => props.visible,
    (newVisibleValue) => {
      isVisible.value = newVisibleValue;
    }
);

watch(
    () => props.enabled,
    (newEnabledValue) => {
      isEnabled.value = newEnabledValue;
    }
);

const onToggle = () => {
  isVisible.value = !isVisible.value;
  emit('update:toggleLayer', {layerId: props.id, visible: isVisible.value});
};

</script>

<template>
  <div v-if="isEnabled" class="layer-control" :class="{ active: visible}" @click="onToggle">
    <div class="layer-icon">
      <svg>
        <use :xlink:href="icon ? `#${icon}` : '#icon-layers'"></use>
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


</style>