var temperature_chart = null;
var humidity_chart = null;

function BuildChart(values, chartTitle, element, backgroundColor, borderColor) {
    var ctx = document.getElementById(element).getContext('2d');
    var myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: chartTitle,
                data: values,
                backgroundColor: backgroundColor,
                borderColor: borderColor
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                xAxes: [{
                    type: 'time',
                    distribution: 'linear',
                    time: {
                        unit: 'hour',
                        displayFormats: {
                            hour: 'H:mm'
                        }
                    },
                    ticks: {
                        major: {
                            enabled: true,
                            fontStyle: 'bold'
                        }
                    }
                }]
            }
        }
    });
    return myChart;
}

function chartsFromTable() {
    // HTML To JSON Script
    // Forked from https://j.hn/html-table-to-json/ with some changes.
    var table = document.getElementById("sensor-readings-table");
    var json = []; // First row needs to be headers.
    var headers = [];
    for (var i = 0; i < table.rows[0].cells.length; i++) {
        headers[i] = table.rows[0].cells[i].id;
    }
    // Go through cells (in reverse).
    for (var i = table.rows.length - 1; i > 0; i--) {
        var tableRow = table.rows[i];
        var rowData = {};
        for (var j = 0; j < tableRow.cells.length; j++) {
            rowData[headers[j]] = tableRow.cells[j].innerHTML;
        }
        json.push(rowData);
    }
    // Map json values back to values array.
    var temperature_data = json.map(function (e) {
        return {x: e.readingdatetime, y: e.temperature};
    });
    var humidity_data = json.map(function (e) {
        return {x: e.readingdatetime, y: e.humidity};
    });
    //console.log(temperature_data);
    //console.log(humidity_data);
    temperature_chart = BuildChart(temperature_data, "Temperature (°C)", "temperature-chart", 'rgba(255, 0, 0, 0.2)', 'rgba(255, 0, 0, 0.8)');
    humidity_chart = BuildChart(humidity_data, "Humidity (%)", "humidity-chart", 'rgba(0, 0, 255, 0.2)', 'rgba(0, 0, 255, 0.8)');
}

window.onload = function () {
    // Build charts on page load.
    chartsFromTable();
}
