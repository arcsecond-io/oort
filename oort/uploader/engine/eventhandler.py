import os
import threading
import time

from watchdog.events import FileSystemEventHandler

from oort.shared.config import get_logger
from oort.shared.identity import Identity
from oort.shared.models import Substatus, Upload, db
from . import packer


class DataFileHandler(FileSystemEventHandler):
    def __init__(self, path: str, identity: Identity, tick=5.0, debug=False):
        super().__init__()
        self._root_path = path
        self._identity = identity
        self._debug = debug
        self._logger = get_logger(debug=self._debug)
        self._tick = tick

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value
        self._logger = get_logger(debug=self._debug)

    @property
    def log_prefix(self) -> str:
        return '[EventHandler: ' + '/'.join(self._root_path.split(os.sep)[-2:]) + ']'

    def launch_restart_loop(self):
        self._logger.info(f'{self.log_prefix} Launching the restart uploads loop (tick = {self._tick} sec).')
        threading.Timer(self._tick, self._restart_uploads).start()

    def _restart_uploads(self):
        with db.atomic():
            count = 0
            for upload in Upload.select() \
                    .where(Upload.substatus == Substatus.RESTART.value | Upload.substatus == Substatus.PENDING.value) \
                    .limit(20):
                count += 1
                pack = packer.UploadPack(self._root_path, upload.file_path, self._identity)
                pack.do_upload()
        self._logger.info(f'{self.log_prefix} Found {count} uploads to restart.')
        threading.Timer(self._tick, self._restart_uploads).start()

    def on_created(self, event):
        if os.path.isfile(event.src_path) and not os.path.basename(event.src_path).startswith('.'):
            self._logger.info(f'{self.log_prefix} Created event for path : {event.src_path}')

            # Protection against large files currently being written, or files being zipped.
            # In both cases, the file size isn't stable yet.
            file_size = -1
            while file_size != os.path.getsize(event.src_path):
                file_size = os.path.getsize(event.src_path)
                time.sleep(0.1)

            # Pack will be identical for file and its zipped counter-part.
            pack = packer.UploadPack(self._root_path, event.src_path, self._identity)

            # Hence if the zipped file is created and being filled, at that point, thanks
            # to the above protection, there is a clear situation: either zip, or upload.
            if pack.should_zip:
                pack.do_zip()
            else:
                pack.do_upload()

    def on_moved(self, event):
        self._logger.info(f'{self.log_prefix} {event.event_type}: {event.src_path}')

    def on_deleted(self, event):
        self._logger.info(f'{self.log_prefix} {event.event_type}: {event.src_path}')

    def on_modified(self, event):
        self._logger.info(f'{self.log_prefix} {event.event_type}: {event.src_path}')
