<script setup>
import {computed, ref} from "vue";
import {useI18n} from 'vue-i18n'
import {breakpointsTailwind, useBreakpoints} from '@vueuse/core'

import {useMapStore} from "@/stores/map";
import LegendItem from "./LegendItem.vue";


const mapStore = useMapStore();

const {t} = useI18n({
  locale: 'en',
  messages: {
    en: {
      legend: {
        title: 'Legend',
      }
    },
    fr: {
      legend: {
        title: 'Légende',
      }
    },
    ar: {
      legend: {
        title: 'مفتاح الخريطة',
      }
    },
    am: {
      legend: {
        title: 'ምስክር',
      }
    },
    es: {
      legend: {
        title: 'Leyenda',
      }
    },
    sw: {
      legend: {
        title: 'Maelezo ya Ramani',
      }
    }
  }
})


const hasLegend = computed(() => {
  return mapStore.visibleLayers.some(layer => layer.legendConfig);
});

const breakpoints = useBreakpoints(breakpointsTailwind)
const isDesktop = breakpoints.greater('md')

const collapsed = ref(false)

</script>

<template>
  <div v-if="hasLegend" class="m-legend" :class="{ 'm-legend-collapsed': collapsed,mobile: !isDesktop }">
    <svg aria-hidden="true" style="position: absolute; width: 0; height: 0; overflow: hidden;">
      <defs>
        <symbol id="icon-arrow-down" viewBox="0 0 38 32"><title>arrow-down</title>
          <path d="M22.2 18.636l9.879-9.879 5.121 4.243-18 18-18-18 5.121-4.243 9.879 9.879v-17.636h6v17.636z"></path>
        </symbol>
        <symbol id="icon-arrow-up" viewBox="0 0 38 32"><title>arrow-up</title>
          <path d="M22.2 13.364l9.879 9.879 5.121-4.243-18-18-18 18 5.121 4.243 9.879-9.879v17.636h6v-17.636z"></path>
        </symbol>
      </defs>
    </svg>
    <div>
      <div v-if="!collapsed">
        <button class="legend-collapse" @click="collapsed = !collapsed">
          <svg class="legend-collapse-icon">
            <use xlink:href="#icon-arrow-down"></use>
          </svg>
        </button>
      </div>
      <button v-if="collapsed" class="legend-expand"
              @click="collapsed = !collapsed">
        <span>{{ t('legend.title') }}</span>
        <svg class="legend-expand-icon">
          <use xlink:href="#icon-arrow-up"></use>
        </svg>
      </button>
    </div>

    <div class="m-legend-wrapper" v-if="!collapsed">
      <div v-for="layer in mapStore.visibleLayers">
        <LegendItem :legend-config="layer.legendConfig" :title="layer.title"/>
      </div>
    </div>

  </div>
</template>


<i18n>
</i18n>

<style>

.m-legend {
  min-width: 150px;
}


.m-legend-wrapper {
  z-index: 1000;
  background-color: white;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  border-radius: 4px 0 4px 4px;
}

.m-legend-item {
  padding: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.legend-collapse {
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: hsla(0, 0%, 44%, .8);
  border: 0;
  border-radius: 2px 2px 0 0;
  bottom: 100%;
  cursor: pointer;
  height: 20px;
  position: absolute;
  right: -1px;
  transform: translateY(-1px);
  width: 40px;
  padding: 0;
}

.legend-collapse-icon {
  height: 14px;
  width: 14px;
  fill: #fff;
}

.legend-expand {
  cursor: pointer;
  width: 100%;
  display: flex;
  justify-content: space-between;
  border: none;
  padding: 10px;
  background: #fff;
  font-size: 13px;
  font-weight: 600;
}


.legend-expand-icon {
  height: 14px;
  width: 14px;
  fill: var(--primary-color);
}

.m-legend.m-legend-collapsed.mobile {
  min-width: 90px;
}

.m-legend.m-legend-collapsed.mobile .legend-expand {
  padding: 10px;
}


</style>