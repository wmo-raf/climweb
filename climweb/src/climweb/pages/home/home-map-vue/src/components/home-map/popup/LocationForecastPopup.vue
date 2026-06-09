<script setup>
import {useMapStore} from "@/stores/map";
import {computed} from "vue";
import {useI18n} from "vue-i18n";

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

const {t} = useI18n({
  inheritLocale: true,
  messages: {
    en: { viewForecast: 'View Forecast' },
    fr: { viewForecast: 'Voir les prévisions' },
    pt: { viewForecast: 'Ver previsão' },
    es: { viewForecast: 'Ver pronóstico' },
    ar: { viewForecast: 'عرض التوقعات' },
    am: { viewForecast: 'የተንቀሳቃሽ እቅድ እይ' },
    sw: { viewForecast: 'Tazama Utabiri' },
  }
});

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
    forecastData.detailUrl = props.locationForecastDetailUrl + citySlug
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
    <div class="location-name">{{ forecastContent.city }}</div>

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

    <a v-if="forecastContent.detailUrl" :href="forecastContent.detailUrl" class="detail-btn">
      {{ t('viewForecast') }}
    </a>

  </div>
</template>

<style scoped>
.popup {
  background-color: white;
  padding: 8px;
  min-width: 100px;
  max-width: 250px;
  display: flex;
    flex-direction: column;
    align-items: center
}

.location-name {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 5px;
}

.condition {
  display: flex;
  align-items: center;
  flex-direction: column;
}

.condition-icon {
  height: 50px;
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
}

.forecast-data-table td.forecast-name  {
  font-weight: 600;
}

.detail-btn {
  display: inline-block;
  margin-top: 8px;
  padding: 5px 12px;
  border-radius: 4px;
  background-color: var(--primary-color, #2563eb);
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  text-decoration: none;
  text-align: center;
  width: 100%;
  box-sizing: border-box;
}

.detail-btn:hover {
  opacity: 0.85;
}

</style>