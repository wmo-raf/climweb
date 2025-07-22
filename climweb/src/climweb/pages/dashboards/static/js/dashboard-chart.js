document.addEventListener("DOMContentLoaded", function () {
    const chartContainers = document.querySelectorAll(".chart-container");

    chartContainers.forEach((container) => {
        const chartId = container.id;
        const dataScriptId = `chart-data-${chartId}`;
        const chartData = JSON.parse(
            document.getElementById(dataScriptId).textContent
        );

        fetchTimeSeriesData("your-layer-id").then((data) => {
            Highcharts.chart(chartId, {
                chart: { type: chartData.chartType || "line" },
                title: { text: chartData.title || "" },
                xAxis: { categories: chartData.categories || [] },
                series: chartData.series || [],
                credits: { enabled: false },
            });
        })
    });

    async function fetchTimeSeriesData(layerId) {
        const url = `/api/raster-data/geostore/timeseries/${layerId}`;

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error("Failed to fetch time series data");

            const json = await response.json();

            // Expected format: [{ timestamp: "2023-01-01T00:00:00Z", value: 12.3 }, ...]
            return json.map((entry) => {
                return [new Date(entry.timestamp).getTime(), entry.value];
            });
        } catch (error) {
            console.error("Error fetching time series data:", error);
            return [];
        }
    }




});
