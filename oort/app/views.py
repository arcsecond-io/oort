import json
import os
import time

from flask import render_template, Response, Blueprint
from flask import current_app as app

from arcsecond import Arcsecond

from oort.app.helpers import AdminLocalState, UploadsLocalState, Context, FileWrapper

main = Blueprint('main', __name__)

DATASET_NAME = 'Oort Uploads'
MAX_SIMULTANEOUS_UPLOADS = 3
UPLOADS = {}


@main.route('/')
@main.route('/index')
def index():
    return render_template('index.html', context=Context(app.config).to_dict())


@main.route('/admin')
def admin():
    state = AdminLocalState(app.config)

    def generate():
        while True:
            state.sync_telescope()
            yield state.get_yield_string()
            state.sync_night_log()
            yield state.get_yield_string()
            time.sleep(300)

    # Using Server-Side Events. See https://blog.easyaspy.org/post/10/2019-04-30-creating-real-time-charts-with-flask
    return Response(generate(), mimetype='text/event-stream')


@main.route('/uploads')
def uploads():
    state = UploadsLocalState(app.config)

    def generate():
        while True:
            state.sync_datasets()
            yield state.get_yield_string()
            time.sleep(1)

    # Using Server-Side Events. See https://blog.easyaspy.org/post/10/2019-04-30-creating-real-time-charts-with-flask
    return Response(generate(), mimetype='text/event-stream')
