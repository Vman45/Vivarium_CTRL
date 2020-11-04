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

import adafruit_dht
import time
import sqlite3
import datetime
import board
import constants
from gpiozero import Energenie


def read_sensor(dht_device, num_retries=3):
    """ Attempt to read from the sensor a set number of times and exit if it fails.
    """
    for attempt_no in range(num_retries):
        try:
            return dht_device.temperature, dht_device.humidity
        except RuntimeError as error:
            if attempt_no < (num_retries - 1):
                print("Sensor read failed.")
                # Need to wait at least 2 seconds before retrying otherwise cached data is returned.
                time.sleep(2)
            else:
                raise error


def to_string(value):
    """ Convert a boolean to on/off as a string.
    """
    if value:
        return "On"
    else:
        return "Off"


def main():

    # Initialise sensor, database connection and cursor.
    dht_device = adafruit_dht.DHT22(board.D4)  # .DHT11(board.D4)
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

        # Read using safe function.
        temperature, humidity = read_sensor(dht_device)

        # Insert readings (or failure) into the database.
        if humidity is not None and temperature is not None:

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
            comments = "Read successful. Heat Mat: " + to_string(heat_mat.value) + ", Fan: " + to_string(fan.value)

        else:

            # Nothing else to do without successful sensor readings. Perhaps fallback code needed for failure.
            comments = "Read failed. Heat Mat: " + to_string(heat_mat.value) + ", Fan: " + to_string(fan.value)

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
