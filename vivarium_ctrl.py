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
import json


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


def is_time_between(begin_time, end_time, check_time=None):
    """ Check if a time is within a range.
        Taken from the accepted answer by Joe Holloway here:
        https://stackoverflow.com/a/10048290
    """
    # If check time is not given, default to current UTC time.
    check_time = check_time or datetime.datetime.utcnow().time()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else:  # Crosses midnight.
        return check_time >= begin_time or check_time <= end_time


def scheduler_loop():

    # Don't share db connection between threads.
    db = sqlite3.connect('vivarium_ctrl.db')
    c = db.cursor()

    # Update device based on schedule.
    while True:
        # Turn the light on if within the on and off time.
        if settings['light-auto']:
            light_state = to_bool(c.execute("SELECT state FROM device_states WHERE device='light'").fetchone()[0])
            light_due_on = is_time_between(settings['light-on-time'], settings['light-off-time'])
            if light_due_on and not light_state:
                c.execute("UPDATE device_states SET state=1 WHERE device='light'")
                db.commit()
            elif not light_due_on and light_state:
                c.execute("UPDATE device_states SET state=0 WHERE device='light'")
                db.commit()
        time.sleep(constants.SCHEDULER_INTERVAL)


def device_and_settings_loop():

    # Don't share db connection between threads.
    db = sqlite3.connect('vivarium_ctrl.db')
    c = db.cursor()

    # Initialise devices.
    heat_mat = Energenie(constants.HEAT_MAT_SOCKET)
    pump = Energenie(constants.PUMP_SOCKET)
    fan = Energenie(constants.FAN_SOCKET)
    light = Energenie(constants.LIGHT_SOCKET)

    # Continue running until interrupted.
    while True:

        #  Update device states.
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

        # Check if settings need reloading.
        reload_settings = to_bool(c.execute("SELECT state FROM flags WHERE flag='reload_settings'").fetchone()[0])
        if reload_settings:
            load_settings()
            c.execute("UPDATE flags SET state = 0 WHERE flag = 'reload_settings'")
            db.commit()

        # Pause briefly.
        time.sleep(constants.DEVICE_AND_SETTINGS_INTERVAL)


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
        if settings['heat-mat-auto']:
            if temperature <= settings['low-temperature'] and not heat_mat_state:
                c.execute("UPDATE device_states SET state=1 WHERE device='heat-mat'")
                db.commit()
                heat_mat_state = True
            elif temperature > settings['low-temperature'] and heat_mat_state:
                c.execute("UPDATE device_states SET state=0 WHERE device='heat-mat'")
                db.commit()
                heat_mat_state = False

        # Turn the fan on if temperature is high.
        fan_state = to_bool(c.execute("SELECT state FROM device_states WHERE device='fan'").fetchone()[0])
        if settings['fan-auto']:
            if temperature >= settings['high-temperature'] and not fan_state:
                c.execute("UPDATE device_states SET state=1 WHERE device='fan'")
                db.commit()
                fan_state = True
            elif temperature < settings['high-temperature'] and fan_state:
                c.execute("UPDATE device_states SET state=0 WHERE device='fan'")
                db.commit()
                fan_state = False

        # Turn the pump on if the humidity is low.
        pump_state = to_bool(c.execute("SELECT state FROM device_states WHERE device='pump'").fetchone()[0])
        if settings['pump-auto']:
            if humidity <= settings['low-humidity'] and not pump_state:
                c.execute("UPDATE device_states SET state=1 WHERE device='pump'")
                db.commit()
                pump_state = True
            elif humidity > settings['low-humidity'] and pump_state:
                c.execute("UPDATE device_states SET state=0 WHERE device='pump'")
                db.commit()
                pump_state = False

        # Light will most likely be on a schedule instead so just fetch the state.
        light_state = to_bool(c.execute("SELECT state FROM device_states WHERE device='light'").fetchone()[0])

        # Write read status and device states to the database.
        comments = "Heat Mat: " + to_string(heat_mat_state) + ", Pump: " + to_string(pump_state) + \
                   ", Fan: " + to_string(fan_state) + ", Light: " + to_string(light_state)

        # Insert and commit.
        c.execute('INSERT INTO sensor_readings VALUES (?,?,?,?)',
                  (datetime.datetime.now(), temperature, humidity, comments))
        db.commit()

        # Sleep until next read.
        time.sleep(constants.SENSOR_MONITOR_INTERVAL)


def load_settings():
    # Load settings.
    f = open('settings.json', 'rt')
    settings.update(json.loads(f.read()))
    # Times will still be string.
    for key in settings.keys():
        if type(settings[key]) == str and ':' in settings[key]:
            settings[key] = datetime.time(int(settings[key].split(':')[0]), int(settings[key].split(':')[1]))


def main():

    # Load initial settings.
    global settings
    settings = dict()
    load_settings()

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

    # Create flags table.
    c.execute('DROP TABLE IF EXISTS flags')
    c.execute('CREATE TABLE flags (flag TEXT, state NUMERIC)')
    c.execute("INSERT INTO flags VALUES ('reload_settings', 0)")
    db.commit()

    # Finished with this connection.
    db.close()

    # Start threads.
    threading.Thread(target=sensor_monitor_loop).start()
    threading.Thread(target=device_and_settings_loop).start()
    threading.Thread(target=scheduler_loop).start()


if __name__ == "__main__":
    main()
