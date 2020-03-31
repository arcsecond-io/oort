import datetime
import json
import os
import time

from flask import render_template, Response, Blueprint
from flask import current_app as app

from arcsecond import Arcsecond

from .models import FileWrapper
from .state import State

main = Blueprint('main', __name__)

DATASET_NAME = 'Oort Uploads'
MAX_SIMULTANEOUS_UPLOADS = 3
UPLOADS = {}


class Context:
    def __init__(self, config):
        self.debug = config['debug']
        self.folder = app.config['folder']
        self.organisation = config['organisation']
        self.telescope = config['telescope']

        self.username = Arcsecond.username(debug=self.debug)
        self.isAuthenticated = Arcsecond.is_logged_in(debug=self.debug)
        self.memberships = Arcsecond.memberships(debug=self.debug)

        self.role = None
        if self.organisation is not None:
            self.role = self.memberships.get(self.organisation, None)

        self.canUpload = self.organisation is None or self.role in ['member', 'admin', 'superadmin']

    def to_dict(self):
        return {'folder': self.folder,
                'isAuthenticated': self.isAuthenticated,
                'username': self.username,
                'organisation': self.organisation,
                'role': self.role,
                'telescope': self.telescope,
                'canUpload': self.canUpload}


@main.route('/')
@main.route('/index')
def index():
    return render_template('index.html', context=Context(app.config).to_dict())


@main.route('/admin')
def admin():
    context = Context(app.config)
    state = State(context.organisation, context.debug)

    def generate():
        admin = {'message': '', 'close': False}
        admin.update(**context.to_dict())

        if context.organisation and context.role:
            # Auto Handling of Night Logs !

            # --- Telescope --

            local_telescope = json.loads(state.read('telescope') or '{}')
            telescopes_api = Arcsecond.build_telescopes_api(debug=context.debug, organisation=context.organisation)

            if local_telescope:
                if local_telescope['uuid'] == context.telescope:
                    admin['telescope'] = local_telescope
                else:
                    telescope = telescopes_api.read(context.telescope)
                    if telescope:
                        admin['telescope'] = local_telescope
                        state.save(telescope=json.dumps(local_telescope))
                        # TODO: check telescope belongs to organisation
                    else:
                        admin['message'] = f"Bummer..."
                        admin['close'] = True

            else:
                if context.telescope:
                    telescope = telescopes_api.read(context.telescope)
                    if telescope:
                        admin['telescope'] = telescope
                        state.save(telescope=json.dumps(telescope))
                        # TODO: check telescope belongs to organisation
                    else:
                        admin['message'] = f"Bummer..."
                        admin['close'] = True
                else:
                    admin['message'] = 'Fetching Organisation\'s Telescopes...'
                    json_data = json.dumps({'admin': admin})
                    yield f"data:{json_data}\n\n"

                    telescopes = telescopes_api.list()
                    if len(telescopes) == 0:
                        admin['message'] = "No telescopes found found."
                    elif len(telescopes) == 1:
                        admin['telescope'] = telescopes[0]
                        state.save(telescope=json.dumps(telescopes[0]))
                    else:
                        admin['message'] = f"Multiple telescopes found. {telescopes}"
                        admin['close'] = True

                    json_data = json.dumps({'admin': admin})
                    yield f"data:{json_data}\n\n"

            date = datetime.datetime.now().date().isoformat()
            admin['date'] = date
            json_data = json.dumps({'admin': admin})
            yield f"data:{json_data}\n\n"

            # --- Night Log --

            log = json.loads(state.read('night_log') or '{}')
            if log:
                admin['night_log'] = log
            else:
                logs_api = Arcsecond.build_nightlogs_api(debug=context.debug, organisation=context.organisation)
                logs = logs_api.list(date=date)

                if len(logs) == 0:
                    admin['message'] = f'Found no Night Log for date {date}. Creating one...'
                elif len(logs) == 1:
                    state.save(night_log=json.dumps(logs[0]))
                    admin['night_log'] = logs[0]
                else:
                    admin['message'] = f'Multiple logs found for date {date}'

                json_data = json.dumps({'admin': admin})
                yield f"data:{json_data}\n\n"

                if len(logs) == 0 and admin['telescope']:
                    print(admin['telescope'])
                    log = logs_api.create({'date': date, 'telescope': admin['telescope']['uuid']})
                    state.save(night_log=json.dumps(log))

            # --- Datasets --

        admin['close'] = True
        json_data = json.dumps({'admin': admin})
        yield f"data:{json_data}\n\n"

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
