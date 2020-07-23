import os

from watchdog.events import FileCreatedEvent
from watchdog.events import FileSystemEventHandler

from oort.shared.config import get_logger


class DataFileHandler(FileSystemEventHandler):
    def __init__(self, path: str):
        super().__init__()
        self._path = path
        self._logger = get_logger()

    def run_initial_walk(self):
        for file in os.listdir(self._path):
            filename = os.path.join(self._path, file)
            event = FileCreatedEvent(filename)
            self.on_created(event)

    def on_created(self, event):
        self._logger.info(f'event type: {event.event_type}  path : {event.src_path}')

    def on_moved(self, event):
        self._logger.info(f'event type: {event.event_type}  path : {event.src_path}')

    def on_deleted(self, event):
        self._logger.info(f'event type: {event.event_type}  path : {event.src_path}')

    def on_modified(self, event):
        self._logger.info(f'event type: {event.event_type}  path : {event.src_path}')
