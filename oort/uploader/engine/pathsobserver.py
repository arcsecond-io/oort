import time
from pathlib import Path
from typing import List

from watchdog.events import FileCreatedEvent
from watchdog.observers import Observer

from oort.shared.config import get_logger
from oort.shared.identity import Identity
from oort.shared.models import Upload
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

    @property
    def log_prefix(self) -> str:
        return '[PathsObserver]'

    def _perform_initial_walk(self, folder_path, event_handler):
        root_path = Path(folder_path)
        # Just in case we pass a file...
        if root_path.is_file():
            root_path = root_path.parent

        count, ignore_count = 0, 0
        for path in root_path.glob('**/*'):
            # Skipping both hidden files and hidden directories.
            if any([part for part in path.parts if len(part) > 0 and part[0] == '.']) or not path.is_file():
                continue
            if Upload.is_finished(str(path)):
                ignore_count += 1
                if ignore_count > 0 and ignore_count % 100 == 0:
                    self._logger.info(f'{self.log_prefix} Ignored {ignore_count} uploads already finished in {folder_path}.')
            else:
                count += 1
                event = FileCreatedEvent(str(path))
                event_handler.dispatch(event)
            time.sleep(0.01)

        self._logger.info(f'{self.log_prefix} Initial walk inside folder {folder_path} dispatched {count} events.')

    def observe_folder(self, folder_path: str, identity: Identity, tick=5.0) -> None:
        event_handler = eventhandler.DataFileHandler(path=folder_path, identity=identity, tick=tick, debug=self._debug)
        self._logger.info(f'{self.log_prefix} Starting initial walk inside folder {folder_path}')
        self._perform_initial_walk(folder_path, event_handler)
        self._logger.info(f'{self.log_prefix} Starting to observe folder {folder_path}')
        watch = self.schedule(event_handler, folder_path, recursive=True)
        self._mapping[folder_path] = {'watcher': watch, 'handler': event_handler}
        event_handler.launch_restart_loop()

    def forget_folder(self, folder_path: str) -> None:
        if folder_path in self._mapping.keys():
            self._logger.info(f'{self.log_prefix} Forgetting to observe folder {folder_path}')
            self.unschedule(self._mapping[folder_path]['watcher'])
            del self._mapping[folder_path]

    @property
    def observed_paths(self) -> List[str]:
        return list(self._mapping.keys())
