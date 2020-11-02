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

# Use HTTPS
HTTPServer.ssl_adapter = BuiltinSSLAdapter(
        certificate='cert/cert.pem',
        private_key='cert/key.pem'
)

# Set URLs
urls = (
    '/', 'index',
    '/login', 'login',
    '/logout', 'logout',
    '/favicon.ico', 'favicon',
    '/stream.mjpg', 'stream'
)

# Setup database connection.
db = web.database(
    dbn='sqlite',
    db='vivarium_ctrl.db'
)

# Templates
render = web.template.render('templates/')

# Debug must be disabled for sessions to work.
web.config.debug = False
app = web.application(urls, globals())
session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'login_state': 0})


class index:
    """ Displays all the data and provide links to other features.
    """
    def GET(self):
        if session.login_state == 0:
            raise web.seeother('/login')
        else:
            # Get last 48 readings (roughly 12 hours).
            sensor_readings = list(db.select('sensor_readings', order='reading_datetime DESC', limit=48))
            # Get the current (or last) temperature and humidity.
            current_temperature = sensor_readings[0]['temperature']
            current_humidity = sensor_readings[0]['humidity']
            # Render with table and charts.
            return render.index(current_temperature, current_humidity, sensor_readings)


class login:
    """ Basic authentication to guard against unauthorised access.
    """
    def GET(self):
        if session.login_state == 0:
            return render.login('')
        else:
            raise web.seeother('/')

    def POST(self):
        username, password = web.input().username, web.input().password
        user = db.select('users', where='username=$username', vars=locals())[0]
        password += user.salt
        password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if user.password == password:
            session.login_state = 1
            raise web.seeother('/')
        else:
            return render.login('Invalid username or password.')


class logout:
    """ Logout from a session.
    """
    def POST(self):
        session.login_state = 0
        session.kill()
        return render.login('Successfully logged out.')


class stream:
    """ Provide an access point for the raw stream.
    """
    def GET(self):
        if session.login_state == 0:
            raise web.seeother('/login')
        else:
            camera = picamera.PiCamera()
            camera.resolution = (1280, 960)
            camera.vflip = True
            web.header('Content-type', 'multipart/x-mixed-replace; boundary=jpgboundary')
            stream = io.BytesIO()
            try:
                for foo in camera.capture_continuous(stream, 'jpeg', burst=True):
                    yield '\r\n--jpgboundary\r\n'
                    web.header('Content-type', 'image/jpeg')
                    yield b'\r\n' + stream.getvalue() + b'\r\n'
                    stream.seek(0)
                    stream.truncate()
            except (KeyboardInterrupt, BrokenPipeError, ConnectionResetError):
                pass
            finally:
                stream.close()
                camera.close()


class favicon:
    """ Redirect requests for a favicon.
    """
    def GET(self):
        raise web.seeother('/static/images/favicon.ico')


if __name__ == "__main__":
    web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", 8181))
