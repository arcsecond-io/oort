import os
import threading
import time

from watchdog.events import FileSystemEventHandler

from oort.shared.config import get_logger
from oort.shared.identity import Identity
from oort.shared.models import Substatus, Upload
from . import packer


class DataFileHandler(FileSystemEventHandler):
    def __init__(self, path: str, identity: Identity, debug=False):
        super().__init__()
        self._root_path = path
        self._identity = identity
        self._debug = debug
        self._logger = get_logger(debug=self._debug)
        threading.Timer(5.0, self._restart_uploads).start()

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value
        self._logger = get_logger(debug=self._debug)

    def _restart_uploads(self):
        for upload in Upload.select().where(Upload.substatus == Substatus.RESTART.value):
            pack = packer.UploadPack(self._root_path, upload.file_path, self._identity, upload=upload)
            pack.do_upload()
        threading.Timer(5.0, self._restart_uploads).start()

    def on_created(self, event):
        if os.path.isfile(event.src_path) and not os.path.basename(event.src_path).startswith('.'):
            self._logger.info(f'Created event for path : {event.src_path}')

            file_size = -1
            while file_size != os.path.getsize(event.src_path):
                file_size = os.path.getsize(event.src_path)
                time.sleep(0.1)

            pack = packer.UploadPack(self._root_path, event.src_path, self._identity)
            pack.do_upload()

    def on_moved(self, event):
        self._logger.info(f'{event.event_type}: {event.src_path}')

    def on_deleted(self, event):
        self._logger.info(f'{event.event_type}: {event.src_path}')

    def on_modified(self, event):
        self._logger.info(f'{event.event_type}: {event.src_path}')
