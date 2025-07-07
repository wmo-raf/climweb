(function () {
    document.addEventListener('DOMContentLoaded', function () {
        const chartTypeField = document.querySelector('[name="chart_type"]');
        const chartColorPanel = document.querySelector('[name="chart_color"]').closest(".w-panel__wrapper");

        function toggleChartColorVisibility() {
            if (chartTypeField.value === 'stripes') {
                chartColorPanel.style.display = 'none';
            } else {
                chartColorPanel.style.display = '';
            }
        }

        if (chartTypeField && chartColorPanel) {
            toggleChartColorVisibility();
            chartTypeField.addEventListener('change', toggleChartColorVisibility);
        }
    });
})();