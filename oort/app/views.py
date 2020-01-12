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
    context = {'isAuthenticated': Arcsecond.is_logged_in(),
               'username': Arcsecond.username(),
               'memberships': Arcsecond.memberships()}
    return render_template('index.html', context=context)


@app.route('/uploads')
def uploads():
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
