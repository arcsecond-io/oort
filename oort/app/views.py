import json
import os
import random
import time

from datetime import datetime
from flask import render_template, Response
from pony.orm import db_session, select, commit

from arcsecond import Arcsecond

from . import app
from .models import Upload, db


@app.route('/')
@app.route('/index')
def index():
    memberships = Arcsecond.memberships()
    organisation, role = list(memberships.items())[0] if len(memberships) == 1 else '', ''

    context = {'isAuthenticated': Arcsecond.is_logged_in(),
               'username': Arcsecond.username(),
               'organisation': organisation,
               'role': role,
               'folder': app.config['folder']}

    return render_template('index.html', context=context)


@app.route('/folders')
def folders():
    return None


# [{'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': random.random() * 100},
#                  {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': random.random() * 100}]

@app.route('/uploads/active')
def uploads_active():
    # Using Server-Side Events. See https://blog.easyaspy.org/post/10/2019-04-30-creating-real-time-charts-with-flask
    @db_session
    def generate():
        while True:
            files = os.listdir(app.config['folder'])
            active_uploads = []

            for file in files:
                u = Upload.get(filepath=file)
                if u is None:
                    active_uploads.append(Upload(filepath=file, filesize=os.path.getsize(file), status='new'))
                elif u.ended is None:
                    active_uploads.append(u)

            json_data = json.dumps([u.to_dict() for u in active_uploads])
            yield f"data:{json_data}\n\n"
            time.sleep(2)

    commit()
    return Response(generate(), mimetype='text/event-stream')


@app.route('/uploads/inactive')
def uploads_inactive():
    @db_session
    def generate():
        while True:
            uploads = select(u for u in Upload if u.ended)
            json_data = json.dumps([u.to_dict() for u in uploads])
            yield f"data:{json_data}\n\n"
            time.sleep(10)

    commit()
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
