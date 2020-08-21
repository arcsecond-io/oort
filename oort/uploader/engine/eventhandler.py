import os
import time

from watchdog.events import FileCreatedEvent
from watchdog.events import FileSystemEventHandler

from oort.shared.config import get_logger
from oort.shared.identity import Identity
from .packer import UploadPack
from .preparator import UploadPreparator
from .scheduler import scheduler


class DataFileHandler(FileSystemEventHandler):
    def __init__(self, path: str, identity: Identity, debug=False):
        super().__init__()
        self._path = path
        self._identity = identity
        self._debug = debug
        self._logger = get_logger(debug=self._debug)

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value
        self._logger = get_logger(debug=self._debug)

    def run_initial_walk(self):
        for file in os.listdir(self._path):
            filename = os.path.join(self._path, file)
            event = FileCreatedEvent(filename)
            self.on_created(event)

    def upload_upon_complete(self, file_path):
        file_size = -1
        while file_size != os.path.getsize(file_path):
            file_size = os.path.getsize(file_path)
            time.sleep(1)

        # file_done = False
        # while not file_done:
        #     try:
        #         os.rename(file_path, file_path)
        #         file_done = True
        #     except:
        #         return True

        pack = UploadPack(self._path, file_path, self._identity.longitude)
        preparator = UploadPreparator(pack=pack, identity=self._identity, debug=self._debug)
        scheduler.prepare_and_upload(preparator)

    def on_created(self, event):
        self._logger.info(f'Created event for path : {event.src_path}')
        self.upload_upon_complete(event.src_path)

    def on_moved(self, event):
        self._logger.info(f'{event.event_type}: {event.src_path}')

    def on_deleted(self, event):
        self._logger.info(f'{event.event_type}: {event.src_path}')

    def on_modified(self, event):
        self._logger.info(f'{event.event_type}: {event.src_path}')
