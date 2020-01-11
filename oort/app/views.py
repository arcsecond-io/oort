import time

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
    uploads = db.Upload.select()
    return render_template('index.html', context=context, uploads=uploads)


@app.route('/progress')
def progress():
    def generate():
        x = 0

        while x <= 100:
            yield "data:" + str(x) + "\n\n"
            x = x + 10
            time.sleep(0.5)

    return Response(generate(), mimetype='text/event-stream')
