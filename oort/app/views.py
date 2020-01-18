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


@app.route('/folders')
def folders():
    return None


# [{'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': random.random() * 100},
#                  {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': random.random() * 100}]

@app.route('/uploads/active')
def uploads_active():
    @db_session
    def generate():
        while True:
            files = os.listdir(folder)
            active_uploads = []

            for file in files:
                filepath = os.path.join(folder, file)
                u = Upload.get(filepath=filepath)
                if u is None:
                    active_uploads.append(Upload(filepath=filepath, filesize=os.path.getsize(filepath), status='new'))
                elif u.ended is None:
                    active_uploads.append(u)
                    u.progress = random.random() * 100
                commit()

            json_data = json.dumps([u.to_dict() for u in active_uploads])
            yield f"data:{json_data}\n\n"
            time.sleep(2)

    commit()
    # Using Server-Side Events. See https://blog.easyaspy.org/post/10/2019-04-30-creating-real-time-charts-with-flask
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
