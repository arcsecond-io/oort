import os

from watchdog.events import FileCreatedEvent
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

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


class PathsObserver(Observer):
    def __init__(self):
        super().__init__()
        self._handler_mapping = {}
        self._watch_mapping = {}

    def add(self, path: str):
        event_handler = DataFileHandler(path=path)
        self._handler_mapping[path] = event_handler
        event_handler.run_initial_walk()
        watch = self.schedule(event_handler, path, recursive=True)
        self._watch_mapping[path] = watch

    def remove(self, path):
        if path in self._watch_mapping.keys():
            self.unschedule(self._watch_mapping[path])


paths_observer = PathsObserver()

if __name__ == "__main__":

    paths_observer.start()

    try:
        while paths_observer.is_alive():
            paths_observer.join(1)
    except KeyboardInterrupt:
        paths_observer.stop()

    paths_observer.join()
