function formatDateTime(datetimeString) {
    const date = new Date(datetimeString);
    const day = date.getDate();
    const month = date.toLocaleString("default", { month: "long" });
    const year = date.getFullYear();
    const hours = date.getHours().toString().padStart(2, "0");
    const minutes = date.getMinutes().toString().padStart(2, "0");
    return `${day} ${month} ${year} ${hours}:${minutes}`;
}

function formatDateTimeJS(datetimeString, formatStr) {
    const date = new Date(datetimeString);

    // Handle custom formats
    switch (formatStr) {
        case "yyyy-MM-dd HH:mm":
            return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
        case "yyyy-MM-dd":
            return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
        case "yyyy-MM":
            return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
        case "MMMM yyyy":
            return `${date.toLocaleString("default", { month: "long" })} ${date.getFullYear()}`;
        case "yyyy":
            return `${date.getFullYear()}`;
        case "pentadal":
            // Example: Jan 2023 - P1 1-5th (customize as needed)
            return pentadalLabel(date);
        case "dekadal":
            // Example: Jan 2023 - D1 1-10th (customize as needed)
            return dekadalLabel(date);
        default:
            return datetimeString;
    }
}

// Helper for pentadal label
function pentadalLabel(date) {
    const day = date.getDate();
    const month = date.toLocaleString("default", { month: "short" });
    const year = date.getFullYear();
    let period = 1, range = "1-5th";
    if (day > 25) { period = 6; range = "26-end"; }
    else if (day > 20) { period = 5; range = "21-25th"; }
    else if (day > 15) { period = 4; range = "16-20th"; }
    else if (day > 10) { period = 3; range = "11-15th"; }
    else if (day > 5) { period = 2; range = "6-10th"; }
    return `${month} ${year} - P${period} ${range}`;
}

// Helper for dekadal label
function dekadalLabel(date) {
    const day = date.getDate();
    const month = date.toLocaleString("default", { month: "short" });
    const year = date.getFullYear();
    let period = 1, range = "1-10th";
    if (day > 20) { period = 3; range = "21-end"; }
    else if (day > 10) { period = 2; range = "11-20th"; }
    return `${month} ${year} - D${period} ${range}`;
}

function initializeCalendar(id, onChange, defaultDates, dateFormat) {
    // Map your custom format to flatpickr's options
    let flatpickrOptions = {
        enableTime: false,
        dateFormat: "Y-m-d",
        mode: "range",
        defaultDate: defaultDates,
        allowInput: true,
        onChange
    };

    // Adjust flatpickr options based on your dateFormat
    switch (dateFormat) {
        case "yyyy":
            flatpickrOptions.dateFormat = "Y";
            flatpickrOptions.plugins = [
                new window.monthSelectPlugin({
                    shorthand: false,
                    dateFormat: "Y",
                    altFormat: "Y",
                    theme: "light"
                })
            ];
            break;
        case "yyyy-MM":
        case "MMMM yyyy":
            flatpickrOptions.dateFormat = "Y-m";
            flatpickrOptions.plugins = [
                new window.monthSelectPlugin({
                    shorthand: false,
                    dateFormat: "Y-m",
                    altFormat: "F Y",
                    theme: "light"
                })
            ];
            break;
        case "yyyy-MM-dd":
            flatpickrOptions.dateFormat = "Y-m-d";
            break;
        case "yyyy-MM-dd HH:mm":
            flatpickrOptions.dateFormat = "Y-m-d H:i";
            flatpickrOptions.enableTime = true;
            break;
        default:
            flatpickrOptions.dateFormat = "Y-m-d";
    }

    flatpickr(`#date-${id}`, flatpickrOptions);
}

function initChart({ chartType, chartId, dataUnit, dateFormat }) {
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
                    return formatDateTimeJS(this.value, dateFormat);
                }
            }
        },
        yAxis: { title: { text: dataUnit } },
        plotOptions: {
            series: {
                lineWidth: 2.5,
                marker: { enabled: false }, // <-- No dots
                turboThreshold: 0, // Optional: for large datasets
            }
        }
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

    const dateFormat = getDateFormatFromContainer(container);


    const chartConfig = {
        chartId,
        chartType: container.dataset.type,
        dataUnit: container.dataset.unit,
        dateFormat
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
    initializeCalendar(chartId, function (selectedDates) {
        updateChartForRange(selectedDates);
    }, defaultDates, dateFormat);

    // Initial chart load (default: oldest to latest)
    updateChartForRange(defaultDates);
}

const warmingStripesColors = [
    "#08306b", "#08519c", "#2171b5", "#4292c6", "#6baed6", "#9ecae1",
    "#c6dbef", "#deebf7", "#f7fbff", "#fff5f0", "#fee0d2", "#fcbba1",
    "#fc9272", "#fb6a4a", "#ef3b2c", "#cb181d", "#99000d"
];

function getStripeColor(val, min, max) {
    // Map value to a color index in the palette
    const percent = (val - min) / (max - min);
    const idx = Math.max(0, Math.min(warmingStripesColors.length - 1, Math.round(percent * (warmingStripesColors.length - 1))));
    return warmingStripesColors[idx];
}

async function renderWarmingStripes(container) {
    const layerId = container.dataset.layerId;
    const adminPath = container.dataset.adminPath;
    if (!layerId || !adminPath) return;

    // Show loading indicator
    container.innerHTML = `<div style="text-align:center;padding:1em;color:#888;display:flex;align-self:center;justify-content:center">Loading...</div>`;

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
    const timeFromDefault = timestamps[timestamps.length - 1];
    const timeToDefault = timestamps[0];

    // Calendar input id logic
    const idSuffix = container.id.replace('stripes-', '');
    const calendarInput = document.querySelector(`#date-stripes-${idSuffix}`);

    // Get date format from container
    const dateFormat = container.dataset.datetimeFormat || "yyyy-MM-dd HH:mm";

    // Helper to fetch and render stripes for a date range
    async function updateStripesForRange(dateRange) {
        let timeFrom, timeTo;
        if (dateRange && dateRange.length === 2) {
            timeFrom = new Date(dateRange[0]).toISOString();
            timeTo = new Date(dateRange[1]).toISOString();
        } else {
            timeFrom = timeFromDefault;
            timeTo = timeToDefault;
        }

        // Show loading while fetching
        container.innerHTML = `<div style="text-align:center;padding:1em;color:#888;display:flex;align-self:center;justify-content:center">Loading...</div>`;

        // Fetch timeseries data for the selected range
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

        // Prepare values and formatted labels
        const values = data.map(d => d.value);
        const labels = data.map(d => formatDateTimeJS(d.date, dateFormat));
        const min = Math.min(...values);
        const max = Math.max(...values);
        const stripeCount = values.length;
        const stripeWidth = (100 / stripeCount) + "%";

        // Render stripes
        const stripesHtml = values.map(val =>
            `<div style="display:inline-block;width:${stripeWidth};height:100%;background:${getStripeColor(val, min, max)};margin:0;padding:0"></div>`
        ).join('');

        // Render labels (show first, last, and every 5th label if not duplicate)
        let labelHtml = '';
        if (stripeCount > 1) {
            labelHtml = labels.map((label, i) => {
                if (
                    i === 0 ||
                    i === stripeCount - 1 ||
                    (i % 5 === 0 && label !== labels[i - 1])
                ) {
                    return `<div style="display:inline-block;width:${stripeWidth};text-align:center;font-size:10px;color:#444;">${label}</div>`;
                } else {
                    return `<div style="display:inline-block;width:${stripeWidth};"></div>`;
                }
            }).join('');
        }

        const years = data.map(d => (new Date(d.date)).getFullYear());
        let yearLabelsHtml = '';
        if (stripeCount > 1) {
            let lastYear = null;
            yearLabelsHtml = years.map((year, i) => {
                // Show first, last, and every 5th year, but only if not a duplicate
                if (
                    i === 0 ||
                    i === stripeCount - 1 ||
                    (year % 5 === 0 && year !== lastYear)
                ) {
                    lastYear = year;
                    // For the last year, align right
                    const style = i === stripeCount - 1
                        ? `display:flex;width:${stripeWidth};justify-content:flex-end;text-align:right;font-size:10px;color:#444;`
                        : `display:flex;width:${stripeWidth};justify-content:flex-start;text-align:center;font-size:10px;color:#444;`;
                    return `<div style="${style}">${year}</div>`;
                } else {
                    lastYear = year;
                    return `<div style="display:flex;width:${stripeWidth};"></div>`;
                }
            }).join('');
        }

        container.innerHTML = `
            <div style="height:100%;display:flex;align-items:stretch;">${stripesHtml}</div>
            <div style="height:18px;display:flex;align-items:flex-start;">${yearLabelsHtml}</div>
        `;
    }

    // Initialize calendar if present
    if (calendarInput) {
        const defaultDates = [
            new Date(timeFromDefault),
            new Date(timeToDefault)
        ];
        if (!calendarInput._flatpickr && window.flatpickr) {
            initializeCalendar(
                `stripes-${idSuffix}`,
                function (selectedDates) {
                    updateStripesForRange(selectedDates);
                },
                defaultDates,
                dateFormat
            );
        }
        if (calendarInput._flatpickr) {
            calendarInput._flatpickr.setDate(defaultDates, true);
        }
    }

    // Initial render with default range
    updateStripesForRange();
}

function getDateFormatFromContainer(container) {
    // Default to ISO if not set
    return container.dataset.datetimeFormat || "yyyy-MM-dd HH:mm";
}

// On DOMContentLoaded, render all stripes charts
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".chart-container").forEach(loadChart);
    document.querySelectorAll(".warming-stripes-chart").forEach(renderWarmingStripes);
});