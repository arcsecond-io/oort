import os

from watchdog.events import FileCreatedEvent
from watchdog.events import FileSystemEventHandler

from oort.shared.config import get_logger
from oort.shared.identity import Identity
from .packer import UploadPack
from .preparator import UploadPreparator
from .scheduler import scheduler


class DataFileHandler(FileSystemEventHandler):
    def __init__(self, path: str, identity: Identity):
        super().__init__()
        self._path = path
        self._identity = identity
        self._logger = get_logger()

    def run_initial_walk(self):
        for file in os.listdir(self._path):
            filename = os.path.join(self._path, file)
            event = FileCreatedEvent(filename)
            self.on_created(event)

    def on_created(self, event):
        self._logger.info(f'event type: {event.event_type}  path : {event.src_path}')
        pack = UploadPack(self._path, event.src_path)
        preparator = UploadPreparator(pack=pack, identity=self._identity)
        scheduler.prepare_and_upload(preparator)

    def on_moved(self, event):
        self._logger.info(f'event type: {event.event_type}  path : {event.src_path}')

    def on_deleted(self, event):
        self._logger.info(f'event type: {event.event_type}  path : {event.src_path}')

    def on_modified(self, event):
        self._logger.info(f'event type: {event.event_type}  path : {event.src_path}')
