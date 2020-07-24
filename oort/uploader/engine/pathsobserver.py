from watchdog.observers import Observer

from oort.shared.identity import Identity
from .eventhandler import DataFileHandler


class PathsObserver(Observer):
    def __init__(self):
        super().__init__()
        self._handler_mapping = {}
        self._watch_mapping = {}

    def start_observe_folder(self, folder_path: str, identity: Identity):
        event_handler = DataFileHandler(path=folder_path, identity=identity)
        self._handler_mapping[folder_path] = event_handler
        event_handler.run_initial_walk()
        watch = self.schedule(event_handler, folder_path, recursive=True)
        self._watch_mapping[folder_path] = watch

    def stop_observe_path(self, path):
        if path in self._watch_mapping.keys():
            self.unschedule(self._watch_mapping[path])
