function BuildChart(labels, values, chartTitle, element, backgroundColor, borderColor) {
    var ctx = document.getElementById(element).getContext('2d');
    var myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: chartTitle,
                data: values,
                backgroundColor: backgroundColor,
                borderColor: borderColor
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true
        }
    });
    return myChart;
}

// Need to wait until table is loaded.
window.onload = function () {
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
    //console.log(json);
    // Map json values back to label array.
    var labels = json.map(function (e) {
        return e.readingdatetime;
    });
    //console.log(labels);
    // Map json values back to values array.
    var temperature_values = json.map(function (e) {
        return e.temperature;
    });
    var humidity_values = json.map(function (e) {
        return e.humidity;
    });
    //console.log(temperature_values);
    var temp_chart = BuildChart(labels, temperature_values, "Temperature", "temperature-chart", 'rgba(0,0,255, 0.2)', 'rgba(0,0,255, 0.8)');
    var humid_chart = BuildChart(labels, humidity_values, "Humidity", "humidity-chart", 'rgba(255,0,0, 0.2)', 'rgba(255,0,0, 0.8)');
}
