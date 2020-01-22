import json
import os
import time

from flask import render_template, Response

from arcsecond import Arcsecond

from . import app
from .models import FileWrapper

DATASET_NAME = 'Oort Uploads'

UPLOADS = {}


@app.route('/')
@app.route('/index')
def index():
    debug = app.config['debug']
    org = app.config['organisation']

    memberships = Arcsecond.memberships(debug=debug)
    role = None
    if org:
        role = memberships.get(org, None)

    context = {'folder': app.config['folder'],
               'isAuthenticated': Arcsecond.is_logged_in(debug=debug),
               'username': Arcsecond.username(debug=debug),
               'organisation': app.config['organisation'],
               'role': role}

    return render_template('index.html', context=context)


def wrap_files(dataset_uuid, autostart=True):
    debug = app.config['debug']
    folder = app.config['folder']

    files = os.listdir(folder)
    for file in files:
        filepath = os.path.join(folder, file)
        print(filepath, dataset_uuid)
        fw = UPLOADS.get(filepath)
        if fw is None:
            fw = FileWrapper(filepath, dataset_uuid, debug)
            UPLOADS[filepath] = fw
            if autostart:
                fw.start()
        else:
            if fw.progress == 100:
                fw.finish()


@app.route('/uploads')
def uploads_active():
    debug = app.config['debug']
    folder = app.config['folder']
    api_datasets = Arcsecond.build_datasets_api(debug=debug)

    all_datasets = api_datasets.list()
    upload_dataset = next((d for d in all_datasets if d['name'] == DATASET_NAME), None)
    if not upload_dataset:
        upload_dataset = api_datasets.create({'name': DATASET_NAME})

    def generate():
        global UPLOADS
        while True:
            wrap_files(upload_dataset['uuid'])
            uploads_data = [fw.to_dict() for fw in UPLOADS.values()]
            json_data = json.dumps({'state': None, 'uploads': uploads_data})
            yield f"data:{json_data}\n\n"
            time.sleep(1)

    # Using Server-Side Events. See https://blog.easyaspy.org/post/10/2019-04-30-creating-real-time-charts-with-flask
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
