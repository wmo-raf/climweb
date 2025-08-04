function formatDateTime(datetimeString) {
    const date = new Date(datetimeString);
    const day = date.getDate();
    const month = date.toLocaleString("default", { month: "long" });
    const year = date.getFullYear();
    const hours = date.getHours().toString().padStart(2, "0");
    const minutes = date.getMinutes().toString().padStart(2, "0");

    return `${day} ${month} ${year} ${hours}:${minutes}`;
}

function initializeCalender(id) {
    flatpickr(`#date-${id}`, {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
        mode: "range"
    });
}



function initChart(chartConfig) {
    const { chartType, chartId, dataUnit } = chartConfig
    const chart = Highcharts.chart(chartId, {
        chart: {
            type: chartType || "line",
            backgroundColor: "transparent",
            spacingTop: 40,
        },
        title: { text: null },
        credits: {
            enabled: false,
        },
        xAxis: {
            labels: {
                formatter: function () {
                    return formatDateTime(this.value);
                },
            },
        },
        yAxis: {
            title: { text: dataUnit },
        },



    });

    // Show loading while fetching
    chart.showLoading('Loading data...');

    return chart
}

function fetchGeostoreID(areaName, level){
    let boundaryURL = "/api/country"
    

    if(level && level === 0){
        fetch(`/api/country`)
            .then(res => res.json())
            .then((data) => {
                return data})
    }
}

function fetchTimeseries() {

}

function renderChartData() {

}

function renderCalendarDates(){

}


document.addEventListener("DOMContentLoaded", function () {
    document
        .querySelectorAll(".chart-container")
        .forEach(function (container) {
            const layerId = container.dataset.layerId;
            const adminCode = container.dataset.adminCode;
            const chartId = container.id;
            const areaDesc = container.dataset.area_desc
            const areaLevel = container.dataset.adminLevel

            initializeCalender(chartId)

            if (!layerId || !adminCode) return;

            let geostoreId = null;
            let oldestDate = null;
            let latestDate = null;
            let chartConfig = {
                chartId: chartId,
                chartType: container.dataset.type,
                dataUnit: container.dataset.unit
            }

            const chart = initChart(chartConfig)


            // Step 1: Get geostore_id
            fetch(`/api/geostore/admin/${adminCode}?thresh=0.005`)
                .then((res) => res.json())
                .then((geo) => {
                    geostoreId = geo?.id;
                    if (!geostoreId)
                        throw new Error("Geostore ID not found");

                    // Step 2: Get timestamps from tiles.json
                    return fetch(`/api/raster/${layerId}/tiles.json`);
                })
                .then((res) => res.json())
                .then((tileJson) => {
                    const timestamps = tileJson?.timestamps || [];
                    if (!timestamps.length)
                        throw new Error("No timestamps available");
                    latestDate = timestamps[0]
                    oldestDate = timestamps[timestamps.length - 1]; // Pick the earliest timestamp

                    // Step 3: Fetch timeseries data with oldest date
                    const timeseriesUrl = `/api/raster-data/geostore/timeseries/${layerId}?geostore_id=${geostoreId}&value_type=mean&time_from=${oldestDate}`;
                    return fetch(timeseriesUrl);
                })
                .then((res) => res.json())
                .then((data) => {
                    const timestamps =
                        data.map((d) => {
                            return d.date;
                        }) || [];

                    const values =
                        data.map((d) => Math.round(d.value * 100) / 100) ||
                        [];

                    chart.xAxis[0].setCategories(timestamps);


                    chart.addSeries(
                        {
                            name: container.dataset.title,
                            color: container.dataset.color,
                            data: values,
                        },
                    );
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





                    // ✅ Hide loading when ready
                    chart.hideLoading();


                })
                .catch((err) => {
                    console.error("Chart load error:", err);
                    container.innerHTML = `<p style="color:red;">Error loading chart</p>`;
                });
        });
});