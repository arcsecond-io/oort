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


@app.route('/folders')
def folders():
    return None


# [{'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': random.random() * 100},
#                  {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': random.random() * 100}]

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

                api = active_uploads.get(filepath)
                if api is None:
                    api = Arcsecond.build_datafiles_api(dataset=upload_dataset['uuid'])
                    api.progress = 0
                    api.filepath = filepath
                    active_uploads[filepath] = api

                    def update_progress(event, progress_percent):
                        print('--->>>>>>>>>', event, progress_percent)
                        api.progress = progress_percent

                    uploader = api.create({'file': filepath}, callback=update_progress)
                    api.uploader = uploader
                    uploader.start()

            json_data = json.dumps(
                [{'filepath': api.filepath, 'progress': api.progress} for api in active_uploads.values()])
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
