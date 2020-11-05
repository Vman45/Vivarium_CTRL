#!/usr/bin/python3

# 
# vivarium_ctrl
# 
# Copyright (c) 2020 Daniel Dean <dd@danieldean.uk>.
# 
# Licensed under The MIT License a copy of which you should have 
# received. If not, see:
# 
# http://opensource.org/licenses/MIT
# 

import adafruit_bme280
import time
import sqlite3
import datetime
import board
import busio
import constants
from gpiozero import Energenie


def to_string(value):
    """ Convert a boolean to on/off as a string.
    """
    if value:
        return "On"
    else:
        return "Off"


def main():

    # Initialise sensor, database connection and cursor.
    i2c = busio.I2C(board.SCL, board.SDA)
    bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
    db = sqlite3.connect('vivarium_ctrl.db')
    c = db.cursor()

    # Initialise devices.
    heat_mat = Energenie(constants.HEAT_MAT_SOCKET)
    fan = Energenie(constants.FAN_SOCKET)

    # Create the sensor readings table if it does not already exist.
    c.execute('CREATE TABLE IF NOT EXISTS sensor_readings (reading_datetime TEXT, temperature NUMERIC, '
              'humidity NUMERIC, comments TEXT)')
    db.commit()

    # Continue running until interrupted.
    while True:

        # Get readings.
        temperature, humidity = round(bme280.temperature, 2), round(bme280.relative_humidity, 2)

        # Turn the heater on if temperature is low.
        if temperature <= constants.LOW_TEMPERATURE and not heat_mat.value:
            heat_mat.on()
        elif temperature > constants.LOW_TEMPERATURE and heat_mat.value:
            heat_mat.off()

        # Turn the fan on if temperature is high.
        if temperature >= constants.HIGH_TEMPERATURE and not fan.value:
            fan.on()
        elif temperature < constants.HIGH_TEMPERATURE and fan.value:
            fan.off()

        # Write read status and device states to the database.
        comments = "Heat Mat: " + to_string(heat_mat.value) + ", Fan: " + to_string(fan.value)

        # Insert and commit.
        c.execute('INSERT INTO sensor_readings VALUES (?,?,?,?)',
                  (datetime.datetime.now(), temperature, humidity, comments))
        db.commit()

        # Exit closing database.
        try:
            # Sleep until next read.
            time.sleep(constants.SLEEP_INTERVAL)
        except KeyboardInterrupt:
            # Close the database on exit.
            db.close()
            print('Database closed.')
            return


if __name__ == "__main__":
    main()
