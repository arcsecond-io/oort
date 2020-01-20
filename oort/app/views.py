import json
import os
import random
import time

from datetime import datetime
from flask import render_template, Response
from pony.orm import db_session, select, commit

from arcsecond import Arcsecond

from . import app
from .models import Upload, db, FileWrapper

DATASET_NAME = 'Oort Uploads'

active_uploads = {}


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


@app.route('/uploads/active')
def uploads_active():
    folder = app.config['folder']
    api_datasets = Arcsecond.build_datasets_api()

    all_datasets = api_datasets.list()
    upload_dataset = next((d for d in all_datasets if d['name'] == DATASET_NAME), None)
    if not upload_dataset:
        upload_dataset = api_datasets.create({'name': DATASET_NAME})

    print(upload_dataset)

    @db_session
    def generate():
        global active_uploads
        while True:
            files = os.listdir(folder)
            for file in files:
                filepath = os.path.join(folder, file)

                fw = active_uploads.get(filepath)
                if fw is None:
                    fw = FileWrapper(filepath, upload_dataset['uuid'])
                    active_uploads[filepath] = fw
                    fw.start()

            json_data = json.dumps([fw.to_dict() for fw in active_uploads.values()])
            yield f"data:{json_data}\n\n"
            time.sleep(1)

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
