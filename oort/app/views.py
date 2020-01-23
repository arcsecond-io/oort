import json
import os
import time

from flask import render_template, Response, Blueprint
from flask import current_app as app

from arcsecond import Arcsecond

from .models import FileWrapper

main = Blueprint('main', __name__)

DATASET_NAME = 'Oort Uploads'
MAX_SIMULTANEOUS_UPLOADS = 3
UPLOADS = {}


@main.route('/')
@main.route('/index')
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
               'organisation': org,
               'role': role}

    return render_template('index.html', context=context)


def wrap_files(debug, folder, dataset_uuid, autostart=True):
    files = os.listdir(folder)
    for file in files:
        filepath = os.path.join(folder, file)
        fw = UPLOADS.get(filepath)
        if fw is None:
            fw = FileWrapper(filepath, dataset_uuid, debug)
            UPLOADS[filepath] = fw

        started_count = len([u for u in UPLOADS.values() if u.started is not None])
        if autostart and started_count < MAX_SIMULTANEOUS_UPLOADS:
            fw.start()
        if fw.started is not None and fw.progress == 100:
            fw.finish()


@main.route('/uploads')
def uploads_active():
    debug = app.config['debug']
    folder = app.config['folder']

    def generate():
        global UPLOADS
        msg = 'Initializing (listing existing Datasets)...'
        state = {'message': msg, 'showTables': False}
        json_data = json.dumps({'state': state, 'uploads': [], 'finished_uploads': []})
        yield f"data:{json_data}\n\n"

        api_datasets = Arcsecond.build_datasets_api(debug=debug)
        all_datasets = api_datasets.list()
        upload_dataset = next((d for d in all_datasets if d['name'] == DATASET_NAME), None)
        if not upload_dataset:
            msg = f'Dataset "{DATASET_NAME}" does not exist. Creating it...'
            state = {'message': msg, 'showTables': False}
            json_data = json.dumps({'state': state, 'uploads': [], 'finished_uploads': []})
            yield f"data:{json_data}\n\n"
            upload_dataset = api_datasets.create({'name': DATASET_NAME})
        else:
            msg = f'Dataset "{DATASET_NAME}" exists. Walking through local files...'
            state = {'message': msg, 'showTables': False}
            json_data = json.dumps({'state': state, 'uploads': [], 'finished_uploads': []})
            yield f"data:{json_data}\n\n"

        while True:
            wrap_files(debug, folder, upload_dataset['uuid'])
            uploads_data = [fw.to_dict() for fw in UPLOADS.values() if fw.is_finished() is False]
            finished_uploads_data = [fw.to_dict() for fw in UPLOADS.values() if fw.is_finished() is True]
            state = {'message': '', 'showTables': True}
            json_data = json.dumps({'state': state, 'uploads': uploads_data, 'finished_uploads': finished_uploads_data})
            yield f"data:{json_data}\n\n"
            time.sleep(1)

    # Using Server-Side Events. See https://blog.easyaspy.org/post/10/2019-04-30-creating-real-time-charts-with-flask
    return Response(generate(), mimetype='text/event-stream')
