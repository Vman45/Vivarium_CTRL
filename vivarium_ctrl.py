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
import threading


def to_string(value):
    """ Convert a boolean to on/off as a string.
    """
    if value:
        return "On"
    else:
        return "Off"


def to_bool(value):
    """ Convert an int (0 or 1) to a boolean.
    """
    if value == 1:
        return True
    else:
        return False


def device_state_loop():

    # Don't share db connection between threads.
    db = sqlite3.connect('vivarium_ctrl.db')
    c = db.cursor()

    # Initialise devices.
    heat_mat = Energenie(constants.HEAT_MAT_SOCKET)
    pump = Energenie(constants.PUMP_SOCKET)
    fan = Energenie(constants.FAN_SOCKET)
    light = Energenie(constants.LIGHT_SOCKET)

    # Check the device states match every second.
    while True:
        device_states = c.execute('SELECT * FROM device_states')
        for device_state in device_states:
            if device_state[0] == 'heat-mat':
                if to_bool(device_state[1]) != heat_mat.value:
                    heat_mat.value = to_bool(device_state[1])
            elif device_state[0] == 'pump':
                if to_bool(device_state[1]) != pump.value:
                    pump.value = to_bool(device_state[1])
            elif device_state[0] == 'fan':
                if to_bool(device_state[1]) != fan.value:
                    fan.value = to_bool(device_state[1])
            elif device_state[0] == 'light':
                if to_bool(device_state[1]) != light.value:
                    light.value = to_bool(device_state[1])
        time.sleep(1)


def sensor_monitor_loop():

    # Initialise sensor, database connection and cursor.
    i2c = busio.I2C(board.SCL, board.SDA)
    bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
    db = sqlite3.connect('vivarium_ctrl.db')
    c = db.cursor()

    # Continue running until interrupted.
    while True:

        # Get readings.
        temperature, humidity = round(bme280.temperature, 2), round(bme280.relative_humidity, 2)

        # Turn the heater on if temperature is low.
        heat_mat_state = to_bool(c.execute("SELECT state FROM device_states WHERE device='heat-mat'").fetchone()[0])
        if temperature <= constants.LOW_TEMPERATURE and not heat_mat_state:
            c.execute("UPDATE device_states SET state=1 WHERE device='heat-mat'")
            db.commit()
            heat_mat_state = True
        elif temperature > constants.LOW_TEMPERATURE and heat_mat_state:
            c.execute("UPDATE device_states SET state=0 WHERE device='heat-mat'")
            db.commit()
            heat_mat_state = False

        # Turn the fan on if temperature is high.
        fan_state = to_bool(c.execute("SELECT state FROM device_states WHERE device='fan'").fetchone()[0])
        if temperature >= constants.HIGH_TEMPERATURE and not fan_state:
            c.execute("UPDATE device_states SET state=1 WHERE device='fan'")
            db.commit()
            fan_state = True
        elif temperature < constants.HIGH_TEMPERATURE and fan_state:
            c.execute("UPDATE device_states SET state=0 WHERE device='fan'")
            db.commit()
            fan_state = False

        # Write read status and device states to the database.
        comments = "Heat Mat: " + to_string(heat_mat_state) + ", Fan: " + to_string(fan_state)

        # Insert and commit.
        c.execute('INSERT INTO sensor_readings VALUES (?,?,?,?)',
                  (datetime.datetime.now(), temperature, humidity, comments))
        db.commit()

        # Sleep until next read.
        time.sleep(constants.SLEEP_INTERVAL)


def main():

    # Initialise database connection and cursor.
    db = sqlite3.connect('vivarium_ctrl.db')
    c = db.cursor()

    # Create the sensor readings table if it does not already exist.
    c.execute('CREATE TABLE IF NOT EXISTS sensor_readings (reading_datetime TEXT, temperature NUMERIC, '
              'humidity NUMERIC, comments TEXT)')
    db.commit()

    # Create a device states table and initialise all as off.
    device_states = [('heat-mat', 0),
                     ('pump', 0),
                     ('fan', 0),
                     ('light', 0)]
    c.execute('DROP TABLE IF EXISTS device_states')
    c.execute('CREATE TABLE device_states (device TEXT, state NUMERIC)')
    c.executemany('INSERT INTO device_states VALUES (?,?)', device_states)
    db.commit()

    # Finished with this connection.
    db.close()

    # Start threads.
    threading.Thread(target=sensor_monitor_loop).start()
    threading.Thread(target=device_state_loop).start()


if __name__ == "__main__":
    main()
