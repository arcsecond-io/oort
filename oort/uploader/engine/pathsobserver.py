from watchdog.observers import Observer

from .eventhandler import DataFileHandler


class PathsObserver(Observer):
    def __init__(self):
        super().__init__()
        self._handler_mapping = {}
        self._watch_mapping = {}

    def start_observe_path(self, path: str):
        event_handler = DataFileHandler(path=path)
        self._handler_mapping[path] = event_handler
        event_handler.run_initial_walk()
        watch = self.schedule(event_handler, path, recursive=True)
        self._watch_mapping[path] = watch

    def stop_observe_path(self, path):
        if path in self._watch_mapping.keys():
            self.unschedule(self._watch_mapping[path])
