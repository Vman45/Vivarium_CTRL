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

function updateCharts(data) {
    if(data.type === "sensor_reading" || data.type === "both") {
        temperature_chart.data.datasets[0].data.push({x: data.sensor_reading.reading_datetime.split(".")[0], y: data.sensor_reading.temperature});
        temperature_chart.data.datasets[0].data.shift();
        temperature_chart.update();
        humidity_chart.data.datasets[0].data.push({x: data.sensor_reading.reading_datetime.split(".")[0], y: data.sensor_reading.humidity});
        humidity_chart.data.datasets[0].data.shift();
        humidity_chart.update();
    };
}

function intToOnOff(value) {
    if(value === 1) {
        return "On";
    } else {
        return "Off";
    }
}

function updateTableAndTiles(data) {
    if(data.type === "sensor_reading" || data.type === "both") {
        $("#sensor-readings-table tbody tr:first").before(
            "<tr>" +
            "   <td>" + data.sensor_reading.reading_datetime.split(".")[0] + "</td>" +
            "   <td>" + data.sensor_reading.temperature + "</td>" +
            "   <td>" + data.sensor_reading.humidity + "</td>" +
            "   <td>" + data.sensor_reading.comments + "</td>" +
            "</td>"
        );
        $("#sensor-readings-table tbody tr:last").remove();
        $("#temperature-tile").text(data.sensor_reading.temperature + "°C");
        $("#humidity-tile").text(data.sensor_reading.humidity + "%");
    };
    if(data.type === "device_states" || data.type === "both") {
        $("#heat-mat-tile input").val(intToOnOff(data.device_states["heat-mat"]));
        $("#pump-tile input").val(intToOnOff(data.device_states.pump));
        $("#fan-tile input").val(intToOnOff(data.device_states.fan));
        $("#light-tile input").val(intToOnOff(data.device_states.light));
    };
}

window.onload = function () {
    // Build the initial charts based on the page load before doing AJAX.
    chartsFromTable();
    // Read an AJAX stream (containing JSON) incrementally.
    // Forked from https://stackoverflow.com/a/18964123 with some additions.
    // Under the CC BY-SA 3.0 licence.
    var last_response_length = false;
    $.ajax("update", {
        xhrFields: {
            onprogress: function(e) {
                var this_response, response = e.currentTarget.response;
                if(last_response_length === false) {
                    this_response = response;
                    last_response_length = response.length;
                } else {
                    this_response = response.substring(last_response_length);
                    last_response_length = response.length;
                }
                console.log("This Response: ", this_response);
                // Parse to JSON, update the table and tiles, then reload the charts.
                data = JSON.parse(this_response);
                updateTableAndTiles(data);
                updateCharts(data);
            }
        }
    })
    .done(function(data) {
        console.log("Complete response: ", data);
    })
    .fail(function(data) {
        console.log("Error: ", data);
    });
    console.log("Request Sent");
}

$(document).ready(function() {
    $(".tile input[type='button']").click(function() {
        var formData = $("form#toggle-device").serializeArray();
        formData.push({name: this.name, value: this.value});
        console.log("Submit Clicked: ", JSON.stringify(formData));
        $.ajax({
            url: "/toggle_device",
            type: "post",
            dataType: "json",
            data: formData,
            success: function(data) {
                // Do nothing.
            }
        });
    });
});
