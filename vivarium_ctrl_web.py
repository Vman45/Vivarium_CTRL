#!/usr/bin/python3

# 
# vivarium_ctrl_web
# 
# Copyright (c) 2020 Daniel Dean <dd@danieldean.uk>.
# 
# Licensed under The MIT License a copy of which you should have 
# received. If not, see:
# 
# http://opensource.org/licenses/MIT
# 

import web
import io
import picamera
from cheroot.server import HTTPServer
from cheroot.ssl.builtin import BuiltinSSLAdapter
import hashlib
import datetime
import time
import json
import logging
from logger import Logger
import sys
import os
import mimetypes

# Use paths relative to the script.
dirname = os.path.dirname(__file__)

logging.basicConfig(
    filename=dirname + '/vivarium_ctrl_web.log',
    format='%(asctime)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    level=logging.INFO
)

sys.stdout = Logger(logging.getLogger(), logging.INFO, '- \[\d+/\w+/\d+ \d+:\d+:\d+] ')
sys.stderr = Logger(logging.getLogger(), logging.ERROR, '- \[\d+/\w+/\d+ \d+:\d+:\d+] ')

# Use HTTPS
HTTPServer.ssl_adapter = BuiltinSSLAdapter(
    certificate=dirname + '/cert/cert.pem',
    private_key=dirname + '/cert/key.pem'
)

# Set URLs
urls = (
    '/', 'Index',
    '/(\d+)', 'Index',
    '/login', 'Login',
    '/logout', 'Logout',
    '/favicon.ico', 'Favicon',
    '/stream.mjpg', 'Stream',
    '/toggle_device', 'ToggleDevice',
    '/settings', 'Settings',
    '/files/(.*)/(.*)', 'Files'
)

# Setup database connection.
db = web.database(
    dbn='sqlite',
    db=dirname + '/vivarium_ctrl.db'
)

# Templates
render = web.template.render(dirname + '/templates/')

# Debug must be disabled for sessions to work.
web.config.debug = False
app = web.application(urls, globals())
session = web.session.Session(app, web.session.DiskStore(dirname + '/sessions'),
                              initializer={'authenticated': False, 'username': None})


class Index:
    """ Displays all the data and provide links to other features.
    """
    def GET(self, num_hours=12):
        if not session.authenticated:
            raise web.seeother('/login')
        else:
            # Calculate date and time by subtracting from timestamp.
            from_datetime = datetime.datetime.fromtimestamp(time.time() - 3600 * int(num_hours))
            # Get requested number of readings.
            sensor_readings = list(db.select('sensor_readings', order='reading_datetime DESC',
                                             where='reading_datetime>=$from_datetime',
                                             vars={'from_datetime': from_datetime}))
            # Get device states.
            device_states = list(db.select('device_states'))
            # Render with table and charts.
            return render.index(device_states, sensor_readings, num_hours)

    def POST(self):
        if not session.authenticated:
            raise web.seeother('/login')
        else:
            num_hours = web.input().num_hours
            if num_hours == '12':
                num_hours = ''
            web.seeother('/' + num_hours)


class Login:
    """ Basic authentication to guard against unauthorised access.
    """
    def GET(self):
        if not session.authenticated:
            return render.login('')
        else:
            raise web.seeother('/')

    def POST(self):
        username, password = web.input().username, web.input().password
        users = db.select('users', where='username=$username', vars=locals())
        # Check if there were any users (only expecting one).
        if users:
            user = users[0]
            password += user.salt
            password = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if user.password == password:
                session.authenticated = True
                session.username = user.username
                logging.info("Successful login by user '" + session.username + "'.")
                raise web.seeother('/')
        # If we made it this far either the username does not exist or the password is wrong.
        logging.warning("Failed login attempt using username '" + username + "'.")
        return render.login('Invalid username or password.')


class Logout:
    """ Logout from a session.
    """
    def POST(self):
        logging.info("Logout by user '" + session.username + "'.")
        session.authenticated = False
        session.username = None
        session.kill()
        return render.login('Successfully logged out.')


class Stream:
    """ Provide an access point for the raw stream.
    """
    def GET(self):
        if not session.authenticated:
            raise web.seeother('/login')
        else:
            camera = picamera.PiCamera()
            camera.resolution = (1280, 960)
            camera.vflip = True
            logging.info("Camera stream opened by user '" + session.username + "'.")
            web.header('Content-type', 'multipart/x-mixed-replace; boundary=jpgboundary')
            stream = io.BytesIO()
            try:
                for foo in camera.capture_continuous(stream, 'jpeg'):
                    yield '\r\n--jpgboundary\r\n'
                    web.header('Content-type', 'image/jpeg')
                    yield b'\r\n' + stream.getvalue() + b'\r\n'
                    stream.seek(0)
                    stream.truncate()
                    time.sleep(0.5)
            except (KeyboardInterrupt, BrokenPipeError, ConnectionResetError):
                pass
            finally:
                logging.info("Camera stream closed by user '" + session.username + "'.")
                stream.close()
                camera.close()


class Favicon:
    """ Redirect requests for a favicon.
    """
    def GET(self):
        raise web.seeother('/files/images/favicon.ico')


class ToggleDevice:
    """ Toggle a devices state.
    """
    def POST(self):
        if not session.authenticated:
            raise web.seeother('/login')
        else:
            device_state = next(iter(web.input().items()))
            logging.info("'" + device_state[0] + "' set '" + device_state[1] + "' by user '" + session.username + "'.")
            if device_state[1] == "On":
                state = 0
            else:
                state = 1
            db.update('device_states', where='device=$device', vars={'device': device_state[0]}, state=state)
            raise web.seeother('/')


class Settings:
    """ Set thresholds and schedules for devices.
    """
    def GET(self):
        if not session.authenticated:
            raise web.seeother('/login')
        else:
            f = open(dirname + '/settings.json', 'rt')
            settings = json.loads(f.read())
            return render.settings(settings, '')

    def POST(self):
        if not session.authenticated:
            raise web.seeother('/login')
        else:
            # Retrieve the input.
            settings = web.input()
            # Correct the types (as they will all be string).
            for key in settings.keys():
                if settings[key] == 'true':
                    settings[key] = True
                elif settings[key] == 'false':
                    settings[key] = False
                elif str.isdigit(settings[key]):
                    settings[key] = float(settings[key])
            # Write to file immediately.
            f = open(dirname + '/settings.json', 'wt')
            f.write(json.dumps(settings, indent=4))
            f.flush()
            # Set reload flag.
            db.update('flags', where="flag='reload_settings'", state=1)
            # Render template with message and new settings.
            logging.info("Settings updated by user '" + session.username + "'.")
            return render.settings(settings, 'Settings updated successfully.')


class Files:
    """ A fairly hackey way to get around the fixed path for static files in webpy.
    """
    def GET(self, path, filename):
        try:
            etag = str(os.path.getmtime(dirname + '/files/' + path + '/' + filename))
            lastmodified = datetime.datetime.fromtimestamp(os.path.getmtime(dirname + '/files/' + path + '/' + filename))
            if web.modified(lastmodified, etag):
                f = open(dirname + '/files/' + path + '/' + filename, 'rb')
                web.header('Content-type', mimetypes.guess_type(filename)[0])
                return f.read()
            else:
                return web.notmodified()
        except (FileNotFoundError, OSError):
            return web.notfound()


if __name__ == "__main__":
    web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", 8181))
