function formatDateTime(datetimeString) {
    const date = new Date(datetimeString);
    const day = date.getDate();
    const month = date.toLocaleString("default", { month: "long" });
    const year = date.getFullYear();
    const hours = date.getHours().toString().padStart(2, "0");
    const minutes = date.getMinutes().toString().padStart(2, "0");
    return `${day} ${month} ${year} ${hours}:${minutes}`;
}

function initializeCalendar(id, onChange, defaultDates) {
    flatpickr(`#date-${id}`, {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
        mode: "range",
        defaultDate: defaultDates,
        allowInput: true, // <-- allow manual typing
        onChange
    });
}

function initChart({ chartType, chartId, dataUnit }) {
    const chart = Highcharts.chart(chartId, {
        chart: {
            type: chartType || "line",
            backgroundColor: "transparent",
            spacingTop: 40,
        },
        title: { text: null },
        credits: { enabled: false },
        xAxis: {
            labels: {
                formatter: function () {
                    return formatDateTime(this.value);
                },
            },
        },
        yAxis: { title: { text: dataUnit } },
    });
    chart.showLoading('Loading data...');
    return chart;
}

async function fetchGeostoreId(adminPath) {
    const res = await fetch(`/api/geostore/admin${adminPath}?thresh=0.005`);
    const geo = await res.json();
    if (!geo?.id) throw new Error("Geostore ID not found");
    return geo.id;
}

async function fetchTimestamps(layerId) {
    const res = await fetch(`/api/raster/${layerId}/tiles.json`);
    const tileJson = await res.json();
    const timestamps = tileJson?.timestamps || [];
    if (!timestamps.length) throw new Error("No timestamps available");
    return timestamps;
}

async function fetchTimeseries(layerId, geostoreId, timeFrom, timeTo) {
    let url = `/api/raster-data/geostore/timeseries/${layerId}?geostore_id=${geostoreId}&value_type=mean`;
    if (timeFrom) url += `&time_from=${timeFrom}`;
    if (timeTo) url += `&time_to=${timeTo}`;
    const res = await fetch(url);
    return res.json();
}

function renderChart(chart, data, container, chartTitle, chartColor, dataUnit) {
    const timestamps = data.map(d => d.date) || [];
    const values = data.map(d => Math.round(d.value * 100) / 100) || [];
    chart.xAxis[0].setCategories(timestamps);
    chart.series.forEach(s => s.remove(false)); // Remove old series
    chart.addSeries({
        name: chartTitle,
        color: chartColor,
        data: values,
        unit: dataUnit,
    });
    chart.update({
        tooltip: {
            formatter: function () {
                return `
                    <b>${this.series.name}</b><br>
                    ${formatDateTime(this.x)} <br> <b>${this.y.toFixed(2)}</b> 
                    ${this.series.options.unit || ""}
                `;
            },
        }
    });
    chart.hideLoading();
}

async function loadChart(container) {
    const layerId = container.dataset.layerId;
    const chartId = container.id;
    const adminPath = container.dataset.adminPath;
    if (!layerId || !adminPath) return;

    const chartConfig = {
        chartId,
        chartType: container.dataset.type,
        dataUnit: container.dataset.unit
    };
    const chart = initChart(chartConfig);

    let geostoreId, timestamps;
    try {
        geostoreId = await fetchGeostoreId(adminPath);
        timestamps = await fetchTimestamps(layerId);
    } catch (err) {
        console.error("Chart load error:", err);
        container.innerHTML = `<p style="color:red;">Error loading chart</p>`;
        return;
    }

    // Set default calendar dates: [oldest, latest]
    const defaultDates = [
        new Date(timestamps[timestamps.length - 1]),
        new Date(timestamps[0])
    ];

    // Helper to fetch and render for a date range
    async function updateChartForRange(dateRange) {
        let timeFrom, timeTo;
        if (dateRange && dateRange.length === 2) {
            timeFrom = new Date(dateRange[0]).toISOString();
            timeTo = new Date(dateRange[1]).toISOString();
        } else {
            // Default: oldest to latest
            timeFrom = timestamps[timestamps.length - 1];
            timeTo = timestamps[0];
        }
        chart.showLoading('Loading data...');
        try {
            const data = await fetchTimeseries(layerId, geostoreId, timeFrom, timeTo);
            renderChart(
                chart,
                data,
                container,
                container.dataset.title,
                container.dataset.color,
                container.dataset.unit
            );
        } catch (err) {
            console.error("Chart load error:", err);
            container.innerHTML = `<p style="color:red;">Error loading chart</p>`;
        }
    }

    // Initialize calendar with default dates and handler
    initializeCalendar(chartId, function(selectedDates) {
        updateChartForRange(selectedDates);
    }, defaultDates);

    // Initial chart load (default: oldest to latest)
    updateChartForRange(defaultDates);
}

async function renderWarmingStripes(container) {
    const layerId = container.dataset.layerId;
    const adminPath = container.dataset.adminPath;
    if (!layerId || !adminPath) return;

    // Fetch geostoreId
    let geostoreId;
    try {
        const res = await fetch(`/api/geostore/admin${adminPath}?thresh=0.005`);
        const geo = await res.json();
        geostoreId = geo.id;
    } catch (err) {
        container.innerHTML = `<p style="color:red;">Error loading stripes</p>`;
        return;
    }

    // Fetch timestamps to determine time_from and time_to
    let timestamps;
    try {
        const res = await fetch(`/api/raster/${layerId}/tiles.json`);
        const tileJson = await res.json();
        timestamps = tileJson?.timestamps || [];
        if (!timestamps.length) throw new Error("No timestamps available");
    } catch (err) {
        container.innerHTML = `<p style="color:red;">Error loading stripes</p>`;
        return;
    }
    const timeFrom = timestamps[timestamps.length - 1];
    const timeTo = timestamps[0];

    // Make sure to use the correct id for the input
    const calendarInput = document.querySelector(
        `#date-${container.id}`
    );

    if (calendarInput) {
        // Initialize flatpickr if not already initialized
        if (!calendarInput._flatpickr && window.flatpickr) {
            flatpickr(calendarInput, {
                enableTime: true,
                dateFormat: "Y-m-d H:i",
                mode: "range",
                allowInput: true
            });
        }
        // Now set the default dates
        if (calendarInput._flatpickr) {
            calendarInput._flatpickr.setDate([new Date(timeFrom), new Date(timeTo)], true);
        }
    }

    // Fetch timeseries data for the full range
    let data;
    try {
        const url = `/api/raster-data/geostore/timeseries/${layerId}?geostore_id=${geostoreId}&value_type=mean&time_from=${timeFrom}&time_to=${timeTo}`;
        const res = await fetch(url);
        data = await res.json();
    } catch (err) {
        container.innerHTML = `<p style="color:red;">Error loading stripes</p>`;
        return;
    }

    if (!Array.isArray(data) || !data.length) {
        container.innerHTML = `<p style="color:red;">No data</p>`;
        return;
    }

    // Get values and min/max for color scaling
    const values = data.map(d => d.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const stripeCount = values.length;
    const stripeWidth = (100 / stripeCount) + "%";

    function getColor(val, min, max) {
        const percent = (val - min) / (max - min);
        const r = Math.round(255 * percent);
        const b = Math.round(255 * (1 - percent));
        return `rgb(${r},0,${b})`;
    }

    container.innerHTML = values.map(val =>
        `<div style="display:inline-block;width:${stripeWidth};height:100%;background:${getColor(val,min,max)};margin:0;padding:0"></div>`
    ).join('');
}

// On DOMContentLoaded, render all stripes charts
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".chart-container").forEach(loadChart);
    document.querySelectorAll(".warming-stripes-chart").forEach(renderWarmingStripes);
});