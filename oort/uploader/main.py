import os
import sys

from watchdog.events import FileCreatedEvent
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from oort.config import get_logger

dir_path = '.'


class DataFileHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self._logger = get_logger()

    def on_moved(self, event):
        self._logger.info(f'event type: {event.event_type}  path : {event.src_path}')

    def on_created(self, event):
        self._logger.info(f'event type: {event.event_type}  path : {event.src_path}')

    def on_deleted(self, event):
        self._logger.info(f'event type: {event.event_type}  path : {event.src_path}')

    def on_modified(self, event):
        self._logger.info(f'event type: {event.event_type}  path : {event.src_path}')


if __name__ == "__main__":

    path = sys.argv[1] if len(sys.argv) > 1 else '.'

    event_handler = DataFileHandler()

    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    for file in os.listdir(dir_path):
        filename = os.path.join(dir_path, file)
        event = FileCreatedEvent(filename)
        event_handler.on_created(event)

    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
