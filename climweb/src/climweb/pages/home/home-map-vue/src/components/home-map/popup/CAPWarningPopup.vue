<script setup>
import {computed} from "vue";
import {format, formatDistanceToNow, parseISO} from "date-fns";

import {useI18n} from 'vue-i18n'

const props = defineProps({
  properties: {
    type: Object,
    required: true
  },
});

const {t} = useI18n()

const alert = computed(() => {
  const alert = {...props.properties}
  if (alert) {
    if (alert.sent) {
      const isoSentDate = parseISO(alert.sent);

      alert.sent = formatDistanceToNow(isoSentDate, {
        addSuffix: true,
      });

      if (alert.onset) {
        const timestamp = Date.parse(alert.onset);
        const date = new Date(timestamp);
        alert.onset = format(date, "MMM dd yyyy, HH:MM");
      } else {
        alert.onset = format(isoSentDate, "MMM dd yyyy, HH:MM");
      }
    }

    if (alert.expires) {
      const timestamp = Date.parse(alert.expires);
      const date = new Date(timestamp);
      alert.expires = format(date, "MMM dd yyyy, HH:MM");
    }
    return alert;
  }
  return null;
})


</script>

<template>
  <div class="popup">
    <div class="alert-severity" :style="{backgroundColor:alert.severity_color}">
      <div class="alert-icon">
        <svg>
          <use xlink:href="#icon-warning"></use>
        </svg>
      </div>
      <div class="alert-severity-label">
        {{ alert.severity }}
      </div>
    </div>
    <div class="alert-meta">
      <div class="alert-meta-item">
        <div class="alert-meta-label">
          {{ t('alert.certainty') }}
        </div>
        <div class="alert-meta-value">
          {{ alert.certainty }}
        </div>
      </div>
      <div class="alert-meta-item">
        <div class="alert-meta-label">
          {{ t('alert.urgency') }}
        </div>
        <div class="alert-meta-value">
          {{ alert.urgency }}
        </div>
      </div>
      <div class="alert-meta-item">
        <div class="alert-meta-label">
          {{ t('alert.sent') }}
        </div>
        <div class="alert-meta-value">
          {{ alert.sent }}
        </div>
      </div>

      <div class="alert-meta-item">
        <div class="alert-meta-label">
          {{ t('alert.onset') }}
        </div>
        <div class="alert-meta-value">
          {{ alert.onset }}
        </div>
      </div>

      <div class="alert-meta-item">
        <div class="alert-meta-label">
          {{ t('alert.expires') }}
        </div>
        <div class="alert-meta-value">
          {{ alert.expires }}
        </div>
      </div>
    </div>
    <div class="alert-detail">
      <div class="alert-event">
        {{ alert.event }}
      </div>
      <div class="alert-headline">
        {{ alert.headline }}
      </div>
    </div>
    <a v-if="alert.web" :href="alert.web" target="_blank" class="alert-link">
      {{ t('alert.moreDetail') }}
    </a>
  </div>
</template>

<style scoped>
.popup {
  background-color: white;
  width: 200px;
}

.alert-severity {
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 5px;
  position: absolute;
  top: 0;
  left: 0;
  padding: 2px 10px;
  color: #fff;
  display: flex;
  align-items: center;
}

.maplibregl-popup-content {
  box-shadow: 0 3px 14px rgba(0, 0, 0, 0.4);
}

.alert-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-right: 5px;
}

.alert-icon svg {
  width: 15px;
  height: 15px;
  fill: #fff;
}

.alert-meta {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding-bottom: 20px
}

.alert-meta-item {
  display: flex;
  gap: 10px;
}

.alert-meta-label {
  min-width: 80px;
  font-weight: 600;
}

.alert-detail {
  margin-top: 20px;
  font-size: 14px;
}

.alert-event {
  font-weight: 600;
  margin-bottom: 8px;
}

.alert-headline {
  margin-bottom: 10px;
  font-size:12px;
}

.alert-link {
  background: var(--text-color);
  color: #fff !important;
  padding: 5px 12px;
  border-radius: 12px;
  text-align: center
}

.alert-link:hover {
  text-decoration: underline;
}


</style>