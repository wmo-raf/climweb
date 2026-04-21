<template>
  <Map :initialBounds="initialBounds" :mapSettingsUrl="mapSettingsUrl" :locationForecastDetailUrl="locationForecastDetailUrl" :primaryColor="primaryColor"/>
</template>

<script setup>
import Map from "./Map.vue";
import {onMounted} from "vue";

const props = defineProps({
  mapSettingsUrl: {
    type: String,
    required: true
  },
  initialBounds: {
    type: String,
    required: false
  },
  locationForecastDetailUrl: {
    type: String,
    required: false
  },
  languageCode: {
    type: String,
    required: false,
    default: 'en'
  },
  homeMapAlertsUrl: {
    type: String,
    required: false
  },
  primaryColor: {
    type: String,
    required: false,
    default: '#000000'
  }
});


const loadAlerts = () => {
  const alertsContainer = document.getElementById('alerts-container');

  if (alertsContainer && props.homeMapAlertsUrl) {
    fetch(props.homeMapAlertsUrl)
        .then(response => {
          if (!response.ok) {
            throw new Error('Error fetching alerts');
          }

          return response.text();
        })
        .then(alertsHTML => {
          const html = new DOMParser().parseFromString(alertsHTML, 'text/html').body
          if (html) {
            alertsContainer.append(html)
            const badge = document.getElementById('alerts-count-badge');
            if (badge) {
              const count = alertsContainer.querySelectorAll('.alert-item').length;
              badge.textContent = count;
              badge.classList.toggle('is-zero', count === 0);
            }
          }
        })
        .catch(error => {
          console.error('Error loading alerts:', error);
        });
  }
}

onMounted(() => loadAlerts());

</script>

<style>
/* Add global styles if needed */
</style>