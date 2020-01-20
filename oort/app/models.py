import os

from pony.orm import Database, Required, Optional, perm
from datetime import datetime

from arcsecond import Arcsecond

db = Database()


class Upload(db.Entity):
    filepath = Required(str, unique=True)
    filesize = Required(int)
    started = Optional(datetime)
    ended = Optional(datetime)
    status = Required(str)
    progress = Required(float, default=0)
    dataset = Optional(str)


with db.set_perms_for(Upload):
    perm('view edit create delete', group='anybody')


class FileWrapper(object):
    def __init__(self, filepath, dataset):
        self.filepath = filepath
        self.dataset = dataset
        self.filesize = os.path.getsize(filepath)
        self.status = 'new'
        self.progress = 0
        self.started = None
        self.ended = None

        self.api = Arcsecond.build_datafiles_api(dataset=dataset)

        def update_progress(event, progress_percent):
            self.progress = progress_percent

        self.uploader = self.api.create({'file': filepath}, callback=update_progress)

    def start(self):
        self.uploader.start()
        self.started = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    def end(self):
        self.ended = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    def to_dict(self):
        return {
            'filepath': self.filepath,
            'filesize': self.filesize,
            'status': self.status,
            'progress': self.progress,
            'started': self.started,
            'ended': self.ended,
            'dataset': self.dataset
        }
