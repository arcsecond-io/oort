import json
import time

from arcsecond import ArcsecondAPI
from flask import Blueprint, Response, render_template, request
from flask import current_app as app, redirect, url_for

from oort.shared.config import get_logger, write_config_value
from oort.shared.models import Status, Substatus, Upload
from .context import Context

logger = get_logger()

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/index')
def index():
    return render_template('index.html', context=app.config['context'].to_dict())


@main.route('/login', methods=['POST'])
def login():
    result, error = ArcsecondAPI.login(request.form.get('username'),
                                       request.form.get('password'),
                                       request.form.get('subdomain'),
                                       debug=app.config['context'].debug)
    app.config['context']['login_error'] = json.loads(error) if error else None
    return redirect(url_for('main.index'))


@main.route('/update')
def update():
    write_config_value('server', 'selected_folder', request.args.get("selectedFolder", ''))
    return Response({}, mimetype='application/json')


@main.route('/uploads')
def uploads():
    # print(app.config)
    context: Context = app.config['context']

    def generate():
        while True:
            yield context.get_yield_string()
            time.sleep(0.5)

    # Using Server-Side Events. See https://blog.easyaspy.org/post/10/2019-04-30-creating-real-time-charts-with-flask
    return Response(generate(), mimetype='text/event-stream')


@main.route('/retry')
def retry():
    ids = request.args.get("ids", '').split(',')
    for upload_id in ids:
        u = Upload.get_by_id(upload_id)
        u.smart_update(status=Status.UPLOADING.value, substatus=Substatus.RESTART.value, error='')
    return Response({}, mimetype='application/json')


@main.route('/ignore')
def ignore():
    ids = request.args.get("ids", '').split(',')
    for upload_id in ids:
        u = Upload.get_by_id(upload_id)
        u.smart_update(status=Status.OK.value, substatus=Substatus.IGNORED.value, error='')
    return Response({}, mimetype='application/json')
