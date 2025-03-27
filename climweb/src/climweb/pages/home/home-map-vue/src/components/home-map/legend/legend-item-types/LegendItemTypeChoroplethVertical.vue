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
  return props.legendConfig && props.legendConfig.type === 'choropleth_vertical' && props.legendConfig.items && props.legendConfig.items.length > 0;
})

</script>

<template>
  <div v-if="enabled" class="m-legend-item">
    <div class="legend-title">{{ props.title }}</div>
    <table>
      <tbody>
      <tr v-for="item in props.legendConfig.items">
        <th>
          <span :style="{backgroundColor: item.color }"></span>
        </th>
        <td>{{ item.name }}</td>
      </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>

.legend-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
}

table tr th {
  padding: 0;
  height: 12px;
  width: 12px;
  border: none;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.12), 0 1px 4px rgba(0, 0, 0, 0.12);
}

table tr th span {
  padding: 0;
  display: inline-block;
  height: 100%;
  width: 100%;
}

table tr td {
  padding: 0 0 4px 8px;
  font-size: 12px;
  line-height: 20px;
  vertical-align: middle;
  border-bottom: none;
}


</style>