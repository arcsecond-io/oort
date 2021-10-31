from pathlib import Path
import threading
import time

from watchdog.events import FileSystemEventHandler

from oort.shared.config import get_oort_logger
from oort.shared.identity import Identity
from oort.shared.models import Substatus, Upload
from . import packer


class DataFileHandler(FileSystemEventHandler):
    def __init__(self, path: Path, identity: Identity, tick=5.0, debug=False):
        super().__init__()
        self._root_path = path
        self._identity = identity
        self._debug = debug
        self._logger = get_oort_logger('uploader', debug=self._debug)
        self._tick = tick

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value
        self._logger = get_oort_logger('uploader', debug=self._debug)

    @property
    def identity(self):
        return self._identity

    @property
    def log_prefix(self) -> str:
        return f'[EventHandler: {str(self._root_path)}]'

    def launch_restart_loop(self):
        self._logger.info(f'{self.log_prefix} Launching the restart uploads loop (tick = {self._tick} sec).')
        threading.Timer(self._tick, self._restart_uploads).start()

    def _restart_uploads(self):
        # with db.atomic():
        count = 0
        for upload in Upload.select().where(
                ((Upload.substatus == Substatus.RESTART.value) |
                 (Upload.substatus == Substatus.PENDING.value)) &
                Upload.file_path.startswith(str(self._root_path))).limit(10):
            count += 1

            pack = packer.UploadPack(str(self._root_path), upload.file_path, self._identity)
            pack.collect_file_info()
            pack.prepare_and_upload_file()  # will take care of zipping
            time.sleep(0.01)

        self._logger.info(f'{self.log_prefix} Found {count} uploads to restart.')
        threading.Timer(self._tick, self._restart_uploads).start()

    def on_created(self, event):
        src_path = Path(event.src_path)

        if src_path.is_file() and not str(src_path.name).startswith('.'):
            relative_path = src_path.relative_to(self._root_path)
            self._logger.info(f'{self.log_prefix} Created event for path : {str(relative_path)}')

            # Protection against large files currently being written, or files being zipped.
            # In both cases, the file size isn't stable yet.
            file_size = -1
            while file_size != src_path.stat().st_size:
                file_size = src_path.stat().st_size
                time.sleep(0.1)

            # Pack will be identical for file and its zipped counterpart.
            pack = packer.UploadPack(str(self._root_path), event.src_path, self._identity)
            # Next line will take care only of parsing file, and preparing Upload DB instance.
            # It should NOT start heavy work, but instead returns quickly to let the initial walk
            # go through the whole file tree.
            pack.collect_file_info()

    def on_moved(self, event):
        relative_path = Path(event.src_path).relative_to(self._root_path)
        self._logger.info(f'{self.log_prefix} {event.event_type}: {str(relative_path)}')

    def on_deleted(self, event):
        relative_path = Path(event.src_path).relative_to(self._root_path)
        self._logger.info(f'{self.log_prefix} {event.event_type}: {str(relative_path)}')

    def on_modified(self, event):
        relative_path = Path(event.src_path).relative_to(self._root_path)
        self._logger.info(f'{self.log_prefix} {event.event_type}: {str(relative_path)}')
