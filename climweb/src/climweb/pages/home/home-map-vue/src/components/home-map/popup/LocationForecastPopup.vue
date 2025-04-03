<script setup>
import {useMapStore} from "@/stores/map";
import {computed} from "vue";

const props = defineProps({
  properties: {
    type: Object,
    required: true
  },
  locationForecastDetailUrl: {
    type: String,
    required: false
  }
});

const mapStore = useMapStore();

const forecastDataParameters = computed(() => {
  return mapStore.forecastSettings?.parameters.reduce((acc, parameter) => {
    acc[parameter.parameter] = parameter
    return acc;
  }, {});
});

const forecastContent = computed(() => {
  if (!forecastDataParameters.value) return null;

  const forecastData = {
    "data": []
  };

  const cityName = props.properties.city;
  const citySlug = props.properties.city_slug;
  const condition = props.properties.condition_label;

  if (props.locationForecastDetailUrl && citySlug) {
    forecastData.detailUrl = cityDetailUrl + citySlug
  }

  if (condition) {
    forecastData.condition = {
      label: condition,
      icon: props.properties.condition_symbol_url
    };
  }

  if (cityName) {
    forecastData.city = cityName;
  }

  for (const parameter in forecastDataParameters.value) {
    const parameterData = props.properties[parameter];

    if (parameterData) {
      const value = parameterData
      const unit = forecastDataParameters.value[parameter].parameter_unit;

      forecastData.data.push({
        value: value,
        name: forecastDataParameters.value[parameter].name,
        unit: unit,
        valueWithUnit: value ? `${value} ${unit}` : null
      })
    }
  }
  return forecastData;
});

</script>

<template>
  <div class="popup" v-if="forecastContent">
    <div class="location-name">
      <a v-if="forecastContent.detailUrl" :href="forecastContent.detailUrl" target="_blank" class="location-detail-url">
        {{ forecastContent.city }}
      </a>
      <span v-else>
        {{ forecastContent.city }}
      </span>
    </div>

    <div v-if="forecastContent.condition" class="condition">
      <figure class="condition-icon">
        <img :src="forecastContent.condition.icon" alt="Condition Icon"/>
      </figure>
      <div class="condition-label">{{ forecastContent.condition.label }}</div>
    </div>
    <div class="forecast-data-table">
      <table>
        <tbody>
        <tr v-for="(item, index) in forecastContent.data" :key="index">
          <td class="forecast-name">{{ item.name }}</td>
          <td class="forecast-value">{{ item.valueWithUnit }}</td>
        </tr>
        </tbody>
      </table>
    </div>

  </div>
</template>

<style scoped>
.popup {
  background-color: white;
  padding: 8px;
  min-width: 100px;
  max-width: 250px;
}

.location-name {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 5px;
  position: absolute;
  top: 8px;
  left: 20px;
}

.location-detail-url {
  text-decoration: underline;
}

.condition {
  display: flex;
  align-items: center;
}

.condition-icon {
  height: 80px;
  margin-right: 5px;
}

.condition-icon img {
  height: 100%;
  object-fit: fill;
}

.condition-label {
  font-size: 14px;
  font-weight: 500;
}

.forecast-data-table {
  margin-top: 4px;
  font-size: 14px;
}


.forecast-data-table td {
  padding: 2px;
  border: 1px solid #ccc;
}

.forecast-value {
  font-weight: 500;
}


</style>