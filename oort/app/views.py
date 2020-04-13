import time

from flask import render_template, Response, Blueprint
from flask import current_app as app

from .uploads import UploadsLocalState
from .helpers import Context

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/index')
def index():
    return render_template('index.html', context=Context(app.config).to_dict())


@main.route('/uploads')
def uploads():
    state = UploadsLocalState(app.config)

    def generate():
        count = 0
        while True:
            if count % 300 == 0:
                yield state.sync_telescopes_and_night_logs()

            if (count < 30 and count % 10 == 0) or count % 60 == 0:
                yield state.sync_observations_and_calibrations()

            yield state.sync_calibrations_uploads()
            yield state.sync_observations_uploads()
            time.sleep(2)
            count += 1

    # Using Server-Side Events. See https://blog.easyaspy.org/post/10/2019-04-30-creating-real-time-charts-with-flask
    return Response(generate(), mimetype='text/event-stream')
