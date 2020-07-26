from typing import List

from watchdog.observers import Observer

from oort.shared.identity import Identity
from .eventhandler import DataFileHandler


class PathsObserver(Observer):
    def __init__(self):
        super().__init__()
        self._mapping = {}

    def start_observe_folder(self, folder_path: str, identity: Identity) -> None:
        event_handler = DataFileHandler(path=folder_path, identity=identity)
        event_handler.run_initial_walk()
        watch = self.schedule(event_handler, folder_path, recursive=True)
        self._mapping[folder_path] = {'watcher': watch, 'handler': event_handler}

    def stop_observe_path(self, folder_path: str) -> None:
        if folder_path in self._mapping.keys():
            self.unschedule(self._mapping[folder_path]['watcher'])
            del self._mapping[folder_path]

    @property
    def observed_paths(self) -> List[str]:
        return list(self._mapping.keys())
