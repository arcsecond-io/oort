import json
import time

from arcsecond import Arcsecond
from flask import current_app as app, redirect, url_for
from flask import render_template, Response, Blueprint, request

from oort.config import get_logger

logger = get_logger()

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/index')
def index():
    return render_template('index.html', context=app.config['context'].to_dict())


@main.route('/login', methods=['POST'])
def login():
    result, error = Arcsecond.login(request.form.get('username'),
                                    request.form.get('password'),
                                    request.form.get('subdomain'),
                                    debug=app.config['context'].debug)
    app.config['login_error'] = json.loads(error) if error else None
    return redirect(url_for('main.index'))


@main.route('/state')
def state():
    context = app.config['context']
    return Response(json.dumps(context.to_dict()), mimetype='application/json')


@main.route('/uploads')
def uploads():
    # print(app.config)
    context = app.config['context']

    def generate():
        while True:
            yield context.get_yield_string()
            time.sleep(1)

    # Using Server-Side Events. See https://blog.easyaspy.org/post/10/2019-04-30-creating-real-time-charts-with-flask
    return Response(generate(), mimetype='text/event-stream')
