# <img src="./static/images/frog-solid.svg" height="50"> Vivarium_CTRL

**Vivarium monitoring and control using a Raspberry Pi.**

![Toad in vivarium.](README.png)

Monitor and control a vivarium to ensure its environment remains optimal for the plants and creatures living in it. 
Currently supports:

- Logging of temperature and humidity from a DHT11 or DHT22 sensor.
- A live camera stream using any compatible camera.
- Presentation via a webpage with HTTPS and secure login.

Future features to include:

- Control up to four devices such as heaters, pumps, fans, etc.
- Manage users via webpage rather than a script.
- Loading as a daemon and logging.

The scripts can (and should) be run in the background using:

```
nohup [Path to file] &
```

This is subject to being broken due to possible future database schema changes.

## Dependencies

You will need to install Adafruit's CircuitPython DHT, webpy and also libgpio2:

```
sudo pip3 install adafruit-circuitpython-dht
sudo pip3 install webpy
sudo apt install libgpio2
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
