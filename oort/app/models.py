import os

from datetime import datetime

from arcsecond import Arcsecond


class FileWrapper(object):
    def __init__(self, filepath, dataset, debug):
        self.filepath = filepath
        self.dataset = dataset
        self.filesize = os.path.getsize(filepath)
        self.status = 'new'
        self.progress = 0
        self.started = None
        self.ended = None
        self.duration = None
        self.result = None
        self.error = None

        self.api = Arcsecond.build_datafiles_api(debug=debug, dataset=dataset)

        def update_progress(event, progress_percent):
            self.progress = progress_percent
            self.duration = (datetime.now() - self.started).total_seconds()

        self.uploader = self.api.create({'file': filepath}, callback=update_progress)

    def start(self):
        if self.started is not None:
            return
        self.uploader.start()
        self.started = datetime.now()

    def finish(self):
        if self.ended is not None:
            return
        self.result, self.error = self.uploader.finish()
        if self.error:
            self.status = 'error'
            self.proress = 0
        else:
            self.status = 'success'
        self.ended = datetime.now()
        self.duration = (self.ended - self.started).total_seconds()

    def is_finished(self):
        return self.ended is not None and (datetime.now() - self.ended).total_seconds() > 2

    def to_dict(self):
        return {
            'filename': os.path.basename(self.filepath),
            'filepath': self.filepath,
            'filesize': self.filesize,
            'status': self.status,
            'progress': self.progress,
            'started': self.started.strftime('%Y-%m-%dT%H:%M:%S') if self.started else '',
            'ended': self.ended.strftime('%Y-%m-%dT%H:%M:%S') if self.ended else '',
            'duration': '{:.1f}'.format(self.duration) if self.duration else '',

            'dataset': self.dataset,
            'error': self.error or ''
        }
