import json
import os
import time

from flask import render_template, Response, Blueprint
from flask import current_app as app

from arcsecond import Arcsecond

from oort.app.helpers import AdminLocalState, Context, FileWrapper

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
            time.sleep(60)

    # Using Server-Side Events. See https://blog.easyaspy.org/post/10/2019-04-30-creating-real-time-charts-with-flask
    return Response(generate(), mimetype='text/event-stream')


def wrap_files(debug, folder, dataset_uuid, autostart=True):
    files = os.listdir(folder)
    for file in files:
        filepath = os.path.join(folder, file)
        fw = UPLOADS.get(filepath)
        if fw is None:
            fw = FileWrapper(filepath, dataset_uuid, debug)
            UPLOADS[filepath] = fw

        started_count = len([u for u in UPLOADS.values() if u.is_started()])
        if autostart and started_count < MAX_SIMULTANEOUS_UPLOADS:
            fw.start()
        if fw.will_finish():
            fw.finish()


@main.route('/uploads')
def uploads():
    config = app.config
    debug = config['debug']
    folder = config['folder']
    canUpload = Context(config).canUpload

    def generate():
        global UPLOADS

        if canUpload is False:
            state = {'message': '', 'showTables': False}
            json_data = json.dumps({'state': state, 'uploads': [], 'finished_uploads': []})
            yield f"data:{json_data}\n\n"

        else:
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
                json_data = json.dumps(
                    {'state': state, 'uploads': uploads_data, 'finished_uploads': finished_uploads_data})
                yield f"data:{json_data}\n\n"
                time.sleep(1)

    # Using Server-Side Events. See https://blog.easyaspy.org/post/10/2019-04-30-creating-real-time-charts-with-flask
    return Response(generate(), mimetype='text/event-stream')
