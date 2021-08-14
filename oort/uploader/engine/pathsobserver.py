import threading
import time
from pathlib import Path
from typing import List

from watchdog.events import FileCreatedEvent
from watchdog.observers import Observer

from oort.shared.config import get_oort_config_upload_folder_sections, get_oort_logger
from oort.shared.constants import OORT_UPLOADER_FOLDER_DETECTION_TICK_SECONDS
from oort.shared.identity import Identity
from oort.shared.models import Upload
from . import eventhandler


class PathsObserver(Observer):
    def __init__(self):
        super().__init__()
        self._mapping = {}
        self._debug = False
        self._logger = get_oort_logger('uploader', debug=self._debug)
        threading.Timer(OORT_UPLOADER_FOLDER_DETECTION_TICK_SECONDS, self._detect_watched_folders).start()

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value
        self._logger = get_oort_logger('uploader', debug=self._debug)
        for folder_path in self._mapping.keys():
            self._mapping[folder_path]['handler'].debug = self._debug

    @property
    def log_prefix(self) -> str:
        return '[PathsObserver]'

    def _detect_watched_folders(self):
        for folder_section in get_oort_config_upload_folder_sections():
            folder_path = folder_section.get('path')
            if folder_path not in self._mapping.keys():
                identity = Identity.from_folder_section(folder_section)
                self._start_watching_folder(folder_path, identity)
        threading.Timer(30, self._detect_watched_folders).start()

    def _start_watching_folder(self, folder_path: str, identity: Identity, tick=5.0) -> None:
        if folder_path in self._mapping.keys():
            self._logger.warn(f'{self.log_prefix} Folder path {folder_path} already observed. Ignoring.')
            return

        self._logger.info(f'{self.log_prefix} Starting to watch folder {folder_path}...')
        event_handler = eventhandler.DataFileHandler(path=folder_path, identity=identity, tick=tick, debug=self._debug)
        watcher = self.schedule(event_handler, folder_path, recursive=True)
        self._mapping[folder_path] = {'watcher': watcher, 'handler': event_handler}

        threading.Thread(target=self._start_initial_walk, args=(folder_path, event_handler)).start()

    def _start_initial_walk(self, folder_path, event_handler):
        self._logger.info(f'{self.log_prefix} Starting initial walk inside folder {folder_path}...')

        root_path = Path(folder_path)
        # Just in case we pass a file...
        if root_path.is_file():
            root_path = root_path.parent

        file_count, event_count, ignore_count = 0, 0, 0
        for path in root_path.glob('**/*'):
            # Skipping both hidden files and hidden directories.
            if any([part for part in path.parts if len(part) > 0 and part[0] == '.']) or not path.is_file():
                continue

            file_count += 1
            if Upload.is_finished(str(path)):
                ignore_count += 1
                if ignore_count > 0 and ignore_count % 100 == 0:
                    self._logger.info(
                        f'{self.log_prefix} Ignored {ignore_count} uploads already finished in {folder_path}.')
            else:
                event_count += 1
                event = FileCreatedEvent(str(path))
                event_handler.dispatch(event)
            time.sleep(0.01)

        if ignore_count < 100:
            self._logger.info(f'{self.log_prefix} Ignored {ignore_count} uploads already finished in {folder_path}.')

        msg = f'{self.log_prefix} Initial walk inside folder {folder_path} '
        msg += f'dispatched {event_count} events for {file_count} files.'
        self._logger.info(msg)

        event_handler.launch_restart_loop()

    def forget_folder(self, folder_path: str) -> None:
        if folder_path in self._mapping.keys():
            self._logger.info(f'{self.log_prefix} Forgetting to observe folder {folder_path}')
            self.unschedule(self._mapping[folder_path]['watcher'])
            del self._mapping[folder_path]

    @property
    def observed_paths(self) -> List[str]:
        return list(self._mapping.keys())
