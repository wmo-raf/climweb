<script setup>
import RadioButton from 'primevue/radiobutton';
import Checkbox from 'primevue/checkbox';
import Select from 'primevue/select';
import FloatLabel from 'primevue/floatlabel';
import {useMapStore} from "@/stores/map";
import {useI18n} from 'vue-i18n'

const mapStore = useMapStore();

const {t} = useI18n({
  locale: 'en',
  messages: {
    en: {
      mapOptions: {
        boundaries: 'Boundaries',
      }
    },
    fr: {
      mapOptions: {
        boundaries: 'Frontières',
      }
    },
    ar: {
      mapOptions: {
        boundaries: 'الحدود',
      }
    },
    am: {
      mapOptions: {
        boundaries: 'ድንበሮች',
      }
    },
    es: {
      mapOptions: {
        boundaries: 'Fronteras',
      }
    },
    sw: {
      mapOptions: {
        boundaries: 'Mipaka',
      }
    }
  }
})


</script>

<template>
  <div class="map-options">
    <div class="basemap-options">
      <div v-for="basemap in mapStore.basemaps" :key="basemap.value" class="basemap-item">
        <RadioButton v-model="mapStore.selectedBasemap" :inputId="basemap.value" name="basemap" :value="basemap.value"
                     class="basemap-input"/>
        <label :for="basemap.value">{{ basemap.label }}</label>
      </div>
    </div>
    <div class="divisor"></div>
    <div class="boundary-check">
      <Checkbox v-model="mapStore.showBoundary" inputId="boundary" name="boundary" value="yes" binary/>
      <label for="boundary" class="boundary-label"> {{ t('mapOptions.boundaries') }} </label>
    </div>
    <div class="divisor"></div>
    <div class="zoom-locations" v-if="mapStore.zoomLocations">
      <label class="zoom-locations-label" for="zoom_location">Zoom Locations</label>
      <Select
          inputId="zoom_location"
          v-model="mapStore.selectedZoomLocation"
          :options="mapStore.zoomLocations"
          optionLabel="name"
          optionValue="id"
          size="small"
          placeholder="Select location"
      />
    </div>
  </div>
</template>

<style scoped>

.map-options {
  font-size: 14px;
}


.basemap-options {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.divisor {
  width: 100%;
  height: 1px;
  border-top: 1px solid rgba(26, 28, 34, .1);
  margin: 15px 0;
}

.basemap-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.boundary-label {
  margin-left: 4px;
}

.zoom-locations {
  display: flex;
  flex-direction: column;
  margin-bottom: 4px;
}

.zoom-locations-label {
  margin-bottom: 4px;
  font-weight: 500;
}

</style>

<style>
.p-checkbox-checked .p-checkbox-box, .p-radiobutton-checked .p-radiobutton-box {
  border-color: var(--primary-color);
  background: var(--primary-color);
}

</style>