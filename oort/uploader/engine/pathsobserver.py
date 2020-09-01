from typing import List

from watchdog.observers import Observer

from oort.shared.config import get_logger
from oort.shared.identity import Identity
from . import eventhandler

class PathsObserver(Observer):
    def __init__(self):
        super().__init__()
        self._mapping = {}
        self._debug = False
        self._logger = get_logger(debug=self._debug)

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value
        self._logger = get_logger(debug=self._debug)
        for folder_path in self._mapping.keys():
            self._mapping[folder_path]['handler'].debug = self._debug

    def observe_folder(self, folder_path: str, identity: Identity) -> None:
        self._logger.info(f'Starting to observe folder {folder_path}')
        event_handler = eventhandler.DataFileHandler(path=folder_path, identity=identity, debug=self._debug)
        watch = self.schedule(event_handler, folder_path, recursive=True)
        self._mapping[folder_path] = {'watcher': watch, 'handler': event_handler}

    def forget_folder(self, folder_path: str) -> None:
        if folder_path in self._mapping.keys():
            self._logger.info(f'Forgetting to observe folder {folder_path}')
            self.unschedule(self._mapping[folder_path]['watcher'])
            del self._mapping[folder_path]

    @property
    def observed_paths(self) -> List[str]:
        return list(self._mapping.keys())
