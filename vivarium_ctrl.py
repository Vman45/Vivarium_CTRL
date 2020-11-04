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


def main():

    # Initialise sensor, database connection and cursor.
    dht_device = adafruit_dht.DHT22(board.D4)  # .DHT11(board.D4)
    db = sqlite3.connect('vivarium_ctrl.db')
    c = db.cursor()

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
            c.execute('INSERT INTO sensor_readings VALUES (?,?,?,?)',
                      (datetime.datetime.now(), temperature, humidity, 'Read successful.'))
        else:
            c.execute('INSERT INTO sensor_readings VALUES (?,?,?,?)',
                      (datetime.datetime.now(), temperature, humidity, 'Read failed.'))
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
