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
            return pentadalLabel(date);
        case "dekadal":
            return dekadalLabel(date);
        default:
            return datetimeString;
    }
}

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

function dekadalLabel(date) {
    const day = date.getDate();
    const month = date.toLocaleString("default", { month: "short" });
    const year = date.getFullYear();
    let period = 1, range = "1-10th";
    if (day > 20) { period = 3; range = "21-end"; }
    else if (day > 10) { period = 2; range = "11-20th"; }
    return `${month} ${year} - D${period} ${range}`;
}

// ------------------ UNIFIED CALENDAR ------------------ //
function initializeCalendar(id, onChange, defaultDates, dateFormat, availableDates = []) {
    const startInputEl = document.querySelector(`#date-start-${id}`);
    const endInputEl = document.querySelector(`#date-end-${id}`);
    let startTimeSelectEl = document.querySelector(`#time-start-${id}`);
    let endTimeSelectEl = document.querySelector(`#time-end-${id}`);


    if (!startInputEl || !endInputEl) {
        console.error(`Start or End date input not found for id: ${id}`);
        return;
    }

    // Map format to vanillajs-datepicker format
    let dpFormat = "yyyy-mm-dd";
    let displayFormat = "yyyy-MM-dd"; // Default display format
    let pickLevel = 0;
     switch (dateFormat) {
        case "yyyy":
            dpFormat = "yyyy";
            displayFormat = "yyyy";
            pickLevel = 2;
            break;
        case "yyyy-MM":
        case "MMMM yyyy":
            dpFormat = "yyyy-mm";
            displayFormat = "yyyy-MM";
            pickLevel = 1;
            break;
        case "yyyy-MM-dd":
            dpFormat = "yyyy-mm-dd";
            displayFormat = "yyyy-MM-dd";
            break;
        case "yyyy-MM-dd HH:mm":
            dpFormat = "yyyy-mm-dd"; // No time support in vanilla-datepicker
            displayFormat = "yyyy-MM-dd";
            break;
        default:
            dpFormat = "yyyy-mm-dd";
            displayFormat = "yyyy-MM-dd";
    }

    const availableDatesSet = new Set(
        availableDates.map((date) => {
          // Create a new Date object and reset the time to midnight (00:00:00)
          const dateWithoutTime = new Date(date);
          dateWithoutTime.setHours(0, 0, 0, 0);
          return formatDateTimeJS(dateWithoutTime, displayFormat);
        })
      );

      // Function to check if a date is available
      const isDateAvailable = (date) => {
        // Ensure the input date also has its time stripped
        const dateWithoutTime = new Date(date);
        dateWithoutTime.setHours(0, 0, 0, 0);
        const formattedDate = formatDateTimeJS(dateWithoutTime, displayFormat);


        return availableDatesSet.has(formattedDate);
      };

    // Initialize start and end datepickers
    const startDatepicker = new Datepicker(startInputEl, {
        format: dpFormat,
        autohide: true,
        todayHighlight: true,
        clearBtn: true,
        pickLevel,
        beforeShowDay: (date) => {
            return isDateAvailable(date) ? { enabled: true } : { enabled: false };
        },
        beforeShowYear: (date) => {
            return isDateAvailable(date) ? { enabled: true } : { enabled: false };
        },
        beforeShowMonth: (date) => {
            return isDateAvailable(date) ? { enabled: true } : { enabled: false };
        },
    });

    const endDatepicker = new Datepicker(endInputEl, {
        format: dpFormat,
        autohide: true,
        todayHighlight: true,
        clearBtn: true,
        pickLevel,
        beforeShowDay: (date) => {
            return isDateAvailable(date) ? { enabled: true } : { enabled: false };
        },
        beforeShowYear: (date) => {
            return isDateAvailable(date) ? { enabled: true } : { enabled: false };
        },
        beforeShowMonth: (date) => {
            return isDateAvailable(date) ? { enabled: true } : { enabled: false };
        },
    });

    // Set default dates if provided
    if (defaultDates && defaultDates.length === 2) {
        startDatepicker.setDate(defaultDates[0]);
        endDatepicker.setDate(defaultDates[1]);
    }

    

    // Populate time selectors if time support is enabled
    if (dateFormat === "yyyy-MM-dd HH:mm") {
        const populateTimeSelector = (timeSelectEl, defaultTime) => {
            const times = [];
            for (let hour = 0; hour < 24; hour++) {
                for (let minute = 0; minute < 60; minute += 15) {
                    const time = `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
                    times.push(time);
                }
            }
            timeSelectEl.innerHTML = times
                .map((time) => `<option value="${time}" ${time === defaultTime ? "selected" : ""}>${time}</option>`)
                .join("");
        };

        if (!startTimeSelectEl) {
            startTimeSelectEl = document.createElement("select");
            startTimeSelectEl.id = `time-start-${id}`;
            startTimeSelectEl.className = "timepicker-select input is-small";
            startInputEl.parentNode.insertBefore(startTimeSelectEl, startInputEl.nextSibling);
        }

        if (!endTimeSelectEl) {
            endTimeSelectEl = document.createElement("select");
            endTimeSelectEl.id = `time-end-${id}`;
            endTimeSelectEl.className = "timepicker-select input is-small";
            endInputEl.parentNode.insertBefore(endTimeSelectEl, endInputEl.nextSibling);
        }

        populateTimeSelector(startTimeSelectEl, "00:00");
        populateTimeSelector(endTimeSelectEl, "23:45");
    }

    // Format the displayed date to be human-friendly
    const formatDisplayDate = (date) => {
        if (!date) return "";
        return formatDateTimeJS(date, displayFormat); // Use formatDateTimeJS for human-friendly formatting
    };

    // Update the input fields with human-friendly dates
    const updateDisplayDates = () => {
        const startDate = startDatepicker.getDate();
        const endDate = endDatepicker.getDate();

        startInputEl.value = formatDisplayDate(startDate);
        endInputEl.value = formatDisplayDate(endDate);
    };

    // Handle date changes
    const handleDateChange = () => {
        const startDate = startDatepicker.getDate();
        const endDate = endDatepicker.getDate();
        const startTime = startTimeSelectEl ? startTimeSelectEl.value : "00:00";
        const endTime = endTimeSelectEl ? endTimeSelectEl.value : "00:00";

        if (startDate && endDate) {
            // Combine date and time into a single ISO string
            const [startHours, startMinutes] = startTime.split(":").map(Number);
            const [endHours, endMinutes] = endTime.split(":").map(Number);

            startDate.setHours(startHours || 0, startMinutes || 0, 0, 0);
            endDate.setHours(endHours || 0, endMinutes || 0, 0, 0);

            // Ensure start date is before or equal to end date
            if (startDate > endDate) {
                console.warn("Start date cannot be after end date");
                return;
            }

            // Trigger the onChange callback with the selected date range
            // onChange && onChange([startDate, endDate]);
            onChange([startDate, endDate]);
        }

        updateDisplayDates();

        
    };

    // Add event listeners for date changes
    startInputEl.addEventListener("changeDate", handleDateChange);
    endInputEl.addEventListener("changeDate", handleDateChange);

    if (startTimeSelectEl) startTimeSelectEl.addEventListener("change", handleDateChange);
    if (endTimeSelectEl) endTimeSelectEl.addEventListener("change", handleDateChange);

}

// ------------------ CHART CODE ------------------ //
function initChart({ chartType, chartId, dataUnit, dateFormat }) {
    const chart = Highcharts.chart(chartId, {
        chart: { type: chartType || "line", backgroundColor: "transparent", spacingTop: 40 },
        title: { text: null },
        credits: { enabled: false },
        xAxis: {
            labels: { formatter: function () { return formatDateTimeJS(this.value, dateFormat); } },
            type: 'datetime',
            tickPixelInterval: 200,
            minTickInterval: 604800000, 
        },
        yAxis: { title: { text: dataUnit || "Y-Axis" } },
        tooltip: {
            formatter: function () {
                const formattedDate = Highcharts.dateFormat('%b %e, %Y %H:%M', this.x); // Tooltip date
                const value = this.y; // The y-value
                return `<b>${formattedDate}</b><br/><b>Value:</b> ${value} ${dataUnit || ""}`;
            },
        },
        plotOptions: {
            series: { lineWidth: chartType === "scatter" ? null : 2.5, marker: { enabled: chartType === "scatter" }, turboThreshold: 0 },
            column: { pointPadding: 0.05, borderWidth: 0, groupPadding: 0.05 },
            scatter: {
                opacity: 0.6,
                marker: { radius: 3.5, symbol: "square", lineWidth: 0.7 },
                jitter: { x: 0.005 }
            },
        }
    });
    chart.showLoading("Loading data...");
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

async function fetchTimeseries(layerId, geostoreId, timeFrom, timeTo, chartType = "line") {
    let url = `/api/raster-data/geostore/timeseries/${layerId}?geostore_id=${geostoreId}&value_type=mean`;
    if (timeFrom) url += `&time_from=${timeFrom}`;
    if (timeTo) url += `&time_to=${timeTo}`;

    const res = await fetch(url);
    const data = await res.json();

    if (chartType === "scatter") {
        return data.map(d => ({ x: new Date(d.date).getTime(), y: d.value }));
    } else {
        return data.map(d => ({ date: d.date, value: d.value }));
    }
}

function renderChart(chart, data, chartTitle, chartColor, dataUnit) {
    if (chart.options.chart.type === "scatter") {
        chart.series.forEach(s => s.remove(false));
        chart.addSeries({ name: chartTitle, color: chartColor, data });
    } else {
        const sortedData = data.sort((a, b) => new Date(a.date) - new Date(b.date));
        const timestamps = sortedData.map(d => new Date(d.date).getTime()) || []; // Use timestamps for datetime xAxis
        const values = sortedData.map(d => Math.round(d.value * 100) / 100) || [];

        
        chart.series.forEach(s => s.remove(false));
        chart.addSeries({ 
            name: chartTitle, 
            color: chartColor, 
            data: timestamps.map((timestamp, i) => [timestamp, values[i]]), // Use [timestamp, value] pairs
            unit: dataUnit });
        

    }
    chart.hideLoading();
}

async function loadChart(container) {
    const layerId = container.dataset.layerId;
    const chartId = container.id;
    const adminPath = container.dataset.adminPath;
    if (!layerId || !adminPath) return;

    const dateFormat = getDateFormatFromContainer(container);
    const chartConfig = { chartId, chartType: container.dataset.type, dataUnit: container.dataset.unit, dateFormat };
    const chart = initChart(chartConfig);

    let geostoreId, timestamps;
    try {
        geostoreId = await fetchGeostoreId(adminPath);
        timestamps = await fetchTimestamps(layerId);
    } catch (err) {
        container.innerHTML = `<p style="color:red;">Error loading chart</p>`;
        return;
    }

    const defaultDates = [new Date(timestamps[timestamps.length - 1]), new Date(timestamps[0])];

    async function updateChartForRange(dateRange) {
        let timeFrom = timestamps[timestamps.length - 1];
        let timeTo = timestamps[0];
        if (dateRange && dateRange.length === 2) {
            timeFrom = new Date(dateRange[0]).toISOString();
            timeTo = new Date(dateRange[1]).toISOString();
        }
        chart.showLoading("Loading data...");
        try {
            const data = await fetchTimeseries(layerId, geostoreId, timeFrom, timeTo, chartConfig.chartType);
            renderChart(chart, data, `${container.dataset.title} (${container.dataset.unit || ""})`, container.dataset.color, container.dataset.unit);
        } catch {
            container.innerHTML = `<p style="color:red;">Error loading chart</p>`;
        }
    }

    initializeCalendar(chartId, updateChartForRange, defaultDates, dateFormat, timestamps.map(ts => new Date(ts).toISOString().split("T")[0]));
    updateChartForRange(defaultDates);
}

// ------------------ WARMING STRIPES ------------------ //
const warmingStripesColors = ["#08306b","#08519c","#2171b5","#4292c6","#6baed6","#9ecae1","#c6dbef","#deebf7","#f7fbff","#fff5f0","#fee0d2","#fcbba1","#fc9272","#fb6a4a","#ef3b2c","#cb181d","#99000d"];

function getStripeColor(val, min, max) {
    const percent = (val - min) / (max - min);
    const idx = Math.max(0, Math.min(warmingStripesColors.length - 1, Math.round(percent * (warmingStripesColors.length - 1))));
    return warmingStripesColors[idx];
}

async function renderWarmingStripes(container) {
    const layerId = container.dataset.layerId;
    const adminPath = container.dataset.adminPath;
    if (!layerId || !adminPath) return;

    container.innerHTML = `<div style="text-align:center;padding:1em;color:#888;">Loading...</div>`;

    let geostoreId;
    try {
        const res = await fetch(`/api/geostore/admin${adminPath}?thresh=0.005`);
        const geo = await res.json();
        geostoreId = geo.id;
    } catch {
        container.innerHTML = `<p style="color:red;">Error loading stripes</p>`;
        return;
    }

    let timestamps;
    try {
        const res = await fetch(`/api/raster/${layerId}/tiles.json`);
        const tileJson = await res.json();
        timestamps = tileJson?.timestamps || [];
        if (!timestamps.length) throw new Error();
    } catch {
        container.innerHTML = `<p style="color:red;">Error loading stripes</p>`;
        return;
    }

    const timeFromDefault = timestamps[timestamps.length - 1];
    const timeToDefault = timestamps[0];
    const idSuffix = container.id.replace("stripes-", "");
    const dateFormat = container.dataset.datetimeFormat || "yyyy-MM-dd";

    async function updateStripesForRange(dateRange) {
        let timeFrom = timeFromDefault, timeTo = timeToDefault;
        if (dateRange && dateRange.length === 2) {
            timeFrom = new Date(dateRange[0]).toISOString();
            timeTo = new Date(dateRange[1]).toISOString();
        }

        container.innerHTML = `<div style="text-align:center;padding:1em;color:#888;">Loading...</div>`;

        let data;
        try {
            const url = `/api/raster-data/geostore/timeseries/${layerId}?geostore_id=${geostoreId}&value_type=mean&time_from=${timeFrom}&time_to=${timeTo}`;
            const res = await fetch(url);
            data = await res.json();
        } catch {
            container.innerHTML = `<p style="color:red;">Error loading stripes</p>`;
            return;
        }

        if (!Array.isArray(data) || !data.length) {
            container.innerHTML = `<p style="color:red;">No data</p>`;
            return;
        }
        data.sort((a, b) => new Date(a.date) - new Date(b.date));

        data.sort((a, b) => new Date(a.date) - new Date(b.date));
        const values = data.map(d => d.value);
        const min = Math.min(...values), max = Math.max(...values);
        const stripeCount = values.length, stripeWidth = (100 / stripeCount) + "%";

        const stripesHtml = values.map(val =>
            `<div style="display:inline-block;width:${stripeWidth};height:100%;background:${getStripeColor(val, min, max)};"></div>`
        ).join("");

        const years = data.map(d => (new Date(d.date)).getFullYear());
        let lastYear = null;
        const yearLabelsHtml = years.map((year, i) => {
            if (i === 0 || i === stripeCount - 1 || (year % 5 === 0 && year !== lastYear)) {
                lastYear = year;
                const style = i === stripeCount - 1
                    ? `display:flex;width:${stripeWidth};justify-content:flex-end;font-size:10px;color:#444;`
                    : `display:flex;width:${stripeWidth};justify-content:flex-start;font-size:10px;color:#444;`;
                return `<div style="${style}">${year}</div>`;
            } else {
                return `<div style="display:flex;width:${stripeWidth};"></div>`;
            }
        }).join("");

        container.innerHTML = `
            <div style="height:100%;display:flex;align-items:stretch;">${stripesHtml}</div>
            <div style="height:18px;display:flex;align-items:flex-start;">${yearLabelsHtml}</div>
        `;
    }

    // ✅ unified calendar init with DateRangePicker
    initializeCalendar(
        `stripes-${idSuffix}`,
        updateStripesForRange,
        [new Date(timeFromDefault), new Date(timeToDefault)],
        dateFormat
    );

    updateStripesForRange([new Date(timeFromDefault), new Date(timeToDefault)]);
}

function getDateFormatFromContainer(container) {
    return container.dataset.datetimeFormat || "yyyy-MM-dd";
}

// ------------------ DOM INIT ------------------ //
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".chart-container").forEach(loadChart);
    document.querySelectorAll(".warming-stripes-chart").forEach(renderWarmingStripes);
});
