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
        self._logger.info(f'Running initial walk for {self._path}')
        for root, _, filenames in os.walk(self._path):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                event = FileCreatedEvent(filepath)
                self.on_created(event)

    def upload_upon_complete(self, file_path):
        file_size = -1
        while file_size != os.path.getsize(file_path):
            file_size = os.path.getsize(file_path)
            time.sleep(0.1)

        # file_done = False
        # while not file_done:
        #     try:
        #         os.rename(file_path, file_path)
        #         file_done = True
        #     except:
        #         return True

        pack = UploadPack(self._path, file_path, self._identity.longitude)
        if pack.is_fits_or_xisf:
            preparator = UploadPreparator(pack=pack, identity=self._identity, debug=self._debug)
            scheduler.prepare_and_upload(preparator)
        else:
            self._logger.info(f'{file_path} not a FITS or XISF. Skipping.')
            pack.archive()

    def on_created(self, event):
        if os.path.isfile(event.src_path) and not os.path.basename(event.src_path).startswith('.'):
            self._logger.info(f'Created event for path : {event.src_path}')
            self.upload_upon_complete(event.src_path)

    def on_moved(self, event):
        self._logger.info(f'{event.event_type}: {event.src_path}')

    def on_deleted(self, event):
        self._logger.info(f'{event.event_type}: {event.src_path}')

    def on_modified(self, event):
        self._logger.info(f'{event.event_type}: {event.src_path}')
