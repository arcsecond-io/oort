import json
import time

from arcsecond import Arcsecond
from flask import current_app as app, redirect, url_for
from flask import render_template, Response, Blueprint, request

from oort.config import get_logger
from .helpers import Context
from .uploads import UploadsLocalState

logger = get_logger()

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/index')
def index():
    app.config['upload_state'] = UploadsLocalState(app.config)
    return render_template('index.html', context=Context(app.config).to_dict())


@main.route('/login', methods=['POST'])
def login():
    result, error = Arcsecond.login(request.form.get('username'),
                                    request.form.get('password'),
                                    request.form.get('subdomain'),
                                    debug=app.config['upload_state'].context.debug)
    app.config['login_error'] = json.loads(error) if error else None
    return redirect(url_for('main.index'))


@main.route('/uploads')
def uploads():
    # print(app.config)
    state = app.config['upload_state']

    def generate():
        count = 0
        yield state.context.get_yield_string()

        while True:
            if state.context.verbose: print(f'Loop count {count}')
            if count % 300 == 0:
                yield from state.sync_telescopes()

            yield from state.sync_calibrations_uploads()
            yield from state.sync_observations_uploads()
            time.sleep(2)
            count += 1

    # Using Server-Side Events. See https://blog.easyaspy.org/post/10/2019-04-30-creating-real-time-charts-with-flask
    return Response(generate(), mimetype='text/event-stream')
