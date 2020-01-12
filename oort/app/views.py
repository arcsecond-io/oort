import json
import random
import time

from datetime import datetime
from flask import render_template, Response
from arcsecond import Arcsecond

from . import app
from .models import db


@app.route('/')
@app.route('/index')
def index():
    memberships = Arcsecond.memberships()
    organisation, role = list(memberships.items())[0] if len(memberships) == 1 else '', ''

    context = {'isAuthenticated': Arcsecond.is_logged_in(),
               'username': Arcsecond.username(),
               'organisation': organisation,
               'role': role,
               'folder': app.config['folder']}

    return render_template('index.html', context=context)

@app.route('/folders')
def folders():
    return None

@app.route('/uploads')
def uploads():
    # Using Server-Side Events. See https://blog.easyaspy.org/post/10/2019-04-30-creating-real-time-charts-with-flask
    def generate():
        while True:
            json_data = json.dumps(
                [{'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': random.random() * 100},
                 {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': random.random() * 100}])
            yield f"data:{json_data}\n\n"
            time.sleep(0.5)

    return Response(generate(), mimetype='text/event-stream')


@app.route('/progress')
def progress():
    def generate():
        x = 0

        while x <= 100:
            yield "data:" + str(x) + "\n\n"
            x = x + 10
            time.sleep(0.5)

    return Response(generate(), mimetype='text/event-stream')
