/*
vivarium_ctrl_web

Copyright (c) 2020 Daniel Dean <dd@danieldean.uk>.

Licensed under The MIT License a copy of which you should have
received. If not, see:

http://opensource.org/licenses/MIT
*/

/*
-------------------------
--------- Login ---------
-------------------------
*/

function login() {

    var username = document.getElementById("username").value;
    var password = document.getElementById("password").value;

    if(username != "" && password != "") {
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
                console.log("Login successful.")
                document.location= "/";
            } else if (this.readyState == 4 && this.status == 401) {
                console.log("Login failed.");
                document.getElementById("login-status").innerHTML = "Invalid username or password.";
            };
        };
        xhttp.open("POST", "/login", true);
        xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        xhttp.send("username=" + username + "&" + "password=" + password);
    };

};

/*
------------------------------------
--------- Live Data Reload ---------
------------------------------------
*/

function reload() {

    setInterval(function() {

        var xhttp = new XMLHttpRequest();

        xhttp.onreadystatechange = function() {
            if(this.readyState == 4 && this.status == 200) {

                // Parse response into JSON.
                var data = JSON.parse(this.responseText);
                // Split for sensor readings.
                var sensorReadings = data.sensor_readings
                // Add and remove sensor readings to/from table and charts.
                var table = document.getElementById("sensor-readings-table");

                for(i = sensorReadings.length - 1; i >= 0; i--) {

                    // Update table.
                    table.deleteRow(-1);
                    var row = table.insertRow(1);
                    row.innerHTML =
                        "<td>" + sensorReadings[i].reading_datetime.split(".")[0] + "</td>" +
                        "<td>" + sensorReadings[i].temperature + "</td>" +
                        "<td>" + sensorReadings[i].humidity + "</td>" +
                        "<td>" + sensorReadings[i].comments + "</td>";

                    // Update charts.
                    temperature_chart.data.datasets[0].data.push({
                        x: sensorReadings[i].reading_datetime.split(".")[0],
                        y: sensorReadings[i].temperature
                    });
                    temperature_chart.data.datasets[0].data.shift();
                    temperature_chart.update();
                    humidity_chart.data.datasets[0].data.push({
                        x: sensorReadings[i].reading_datetime.split(".")[0],
                        y: sensorReadings[i].humidity
                     });
                    humidity_chart.data.datasets[0].data.shift();
                    humidity_chart.update();

                };

                // Split device states and update tiles.
                var deviceStates = data.device_states;
                for(i = 0; i < deviceStates.length; i++) {
                    document.getElementById(deviceStates[i].device).value = deviceStates[i].state;
                };

            } else if(this.readyState == 4 && this.status == 401) {
                //console.log("Session expired.");
                document.location = "/login";
            } else if(this.readyState == 4 && this.status == 304) {
                //console.log("No changes.")
            };
        };

        var fromDateTime = Date.parse(document.getElementById("sensor-readings-table").rows[1].cells[0].innerHTML);
        fromDateTime = Math.ceil(fromDateTime / 1000) + 1;  // + 1 to account for truncated fractions of a second.
        xhttp.open("POST", "/reload", true);
        xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        xhttp.send("last=" + fromDateTime);

    }, 5000);

};
