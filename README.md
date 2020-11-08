# <img src="./static/images/frog-solid.svg" height="50"> Vivarium_CTRL

**Vivarium monitoring and control using a Raspberry Pi.**

![Web interface screenshot.](README.png)

Monitor and control a vivarium to ensure its environment remains optimal for the plants and creatures living in it. 
Currently supports:

- Logging of temperature and humidity from a BME280 sensor.
- A live camera stream using any compatible camera.
- Presentation via a webpage with HTTPS and secure login.
- Control up to four devices such as heaters, pumps, fans, etc.
- Automated device control based on time, humidity and temperature.

Future features to include:

- Manage users via webpage rather than a script.
- Loading as a daemon and logging.

The scripts can (and should) be run in the background using:

```
nohup [Path to file] &
```

This is subject to being broken due to possible future database schema changes.

## Hardware

I am using the following:

- Raspberry Pi Zero WH
- MakerHawk Night Vision IR-Cut FishEye Camera
- WaveShare BME280
- Energenie PiMote
- Energenie Four-way Trailing Gang

Guidance on putting it all together to follow at some stage.

## Dependencies

You will need to install Adafruit's CircuitPython BME280, webpy and gpiozero:

```
sudo pip3 install adafruit-circuitpython-bme280
sudo pip3 install webpy
sudo pip3 install gpiozero
```

## Credits

This project contains icons from [Font Awesome](https://fontawesome.com/) licensed under the 
[CC BY 4.0 license](https://creativecommons.org/licenses/by/4.0/) and an image used as the background 
by [Ryan Mandelbaum](https://flic.kr/p/2baRkwQ) licensed under the 
[CC BY 2.0 license](https://creativecommons.org/licenses/by/2.0/).

[Chart.js](https://www.chartjs.org/) is used to produce the temperature and humidity charts. It is also licensed under 
the MIT license. It is included rather than fetched as I am likely to run this project locally.

Javascript forked from [HTML Table To JSON](https://j.hn/html-table-to-json/) is used to extract data from the sensor 
readings table to enable client side chart creation.

A function called ```is_time_between``` included in ```vivirium_ctrl.py``` is from the accepted answer given by Joe 
Holloway [to this question on Stack Overflow](https://stackoverflow.com/a/10048290), it is licensed under the 
[CC BY-SA 4.0 license](https://creativecommons.org/licenses/by-sa/4.0/).
