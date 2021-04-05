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
