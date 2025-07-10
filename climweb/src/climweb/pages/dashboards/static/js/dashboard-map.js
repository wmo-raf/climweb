// File: static/js/dashboard-map.js

document.querySelectorAll('.map-container[data-layer-type="raster"]').forEach(container => {
  const containerId = container.id;
  const tileJson = JSON.parse(document.getElementById(`tilejson-data-${containerId}`).textContent);
  const layerConfig = JSON.parse(document.getElementById(`layer-config-${containerId}`).textContent);
  const legendConfig = JSON.parse(document.getElementById(`legend-data-${containerId}`).textContent);

  const map = new maplibregl.Map({
    container: containerId,
    style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
    center: [36.8219, -1.2921],
    zoom: 3,
    scrollZoom: false
  });

  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
  map.addControl(new maplibregl.FullscreenControl(), 'top-right');
  map.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-left');

  const timestamps = tileJson.timestamps?.slice(-10) || [];
  const latestTimestamp = timestamps[0];
  const timeParam = tileJson.time_parameter || 'time';

  const sourceId = `raster-source-${containerId}`;
  const layerId = `raster-layer-${containerId}`;

  function updateLayer(time) {
    if (map.getLayer(layerId)) map.removeLayer(layerId);
    if (map.getSource(sourceId)) map.removeSource(sourceId);

    const tilesWithTime = tileJson.tiles.map(tile => `${tile}?${timeParam}=${encodeURIComponent(time)}`);

    map.addSource(sourceId, {
      type: 'raster',
      tiles: tilesWithTime,
      tileSize: tileJson.tileSize || 256,
      attribution: tileJson.attribution || ''
    });

    map.addLayer({
      id: layerId,
      type: 'raster',
      source: sourceId,
      paint: layerConfig.paint || { 'raster-opacity': 0.85 }
    });
  }

  map.on('load', () => {
    updateLayer(latestTimestamp);
  });

  // Slider setup
  const sliderWrapper = container.closest('.dashboard-map').querySelector('.map-time-slider');
  const slider = sliderWrapper.querySelector('input[type="range"]');
  const sliderLabel = sliderWrapper.querySelector('.slider-value');
  const datalist = sliderWrapper.querySelector('datalist');

  slider.max = timestamps.length - 1;
  slider.value = 0;
  slider.disabled = false;

  sliderLabel.textContent = new Date(latestTimestamp).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  });

  // Create ticks
  datalist.innerHTML = '';
  timestamps.forEach((timestamp, index) => {
    const option = document.createElement('option');
    option.value = index;
    option.label = new Date(timestamp).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric'
    });
    datalist.appendChild(option);
  });

  slider.addEventListener('input', () => {
    const selectedIndex = parseInt(slider.value);
    const selectedTime = timestamps[selectedIndex];
    sliderLabel.textContent = new Date(selectedTime).toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
    updateLayer(selectedTime);
  });

  // Legend setup
  if (legendConfig && legendConfig.items?.length) {
    const legendContainer = container.closest('.dashboard-map').querySelector('.map-legend');
    legendContainer.innerHTML = legendConfig.items.map(item => `
      <div class="legend-item">
        <span class="color" style="background-color: ${item.color}"></span>
        <span class="label">${item.name || item.value}</span>
      </div>
    `).join('');
  }
});
