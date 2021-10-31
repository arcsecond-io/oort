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
from oort.shared.utils import is_hidden
from . import eventhandler


class PathsObserver(Observer):
    def __init__(self):
        super().__init__()
        self._mapping = {}
        self._debug = False
        self._logger = get_oort_logger('uploader', debug=self._debug)
        self._handler_tick = 20.0
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
        mapping_keys = self._mapping.keys()
        folder_sections = get_oort_config_upload_folder_sections()

        # Unschedule all paths that are not observed anymore.
        folder_section_paths = [section.get('path') for section in folder_sections]
        for mapping_key in mapping_keys:
            if mapping_key not in folder_section_paths:
                self.unschedule(mapping_key)

        # Now, schedule, if not yet done, all folders to be watched.
        for folder_section in folder_sections:
            folder_path = folder_section.get('path')
            identity = Identity.from_folder_section(folder_section)

            if folder_path in mapping_keys:
                # Folder is already watched. We need to update its config only if identity is different.
                handler = self._mapping.get(folder_path).get('handler')
                if handler is not None and identity != handler.identity:
                    self._unschedule_watch(folder_path)
                    self._schedule_watch(folder_path, identity, initial_walk=False)
            else:
                self._schedule_watch(folder_path, identity, initial_walk=True)

        # Every OORT_UPLOADER_FOLDER_DETECTION_TICK_SECONDS seconds, new folders are being checked.
        threading.Timer(OORT_UPLOADER_FOLDER_DETECTION_TICK_SECONDS, self._detect_watched_folders).start()

    def _unschedule_watch(self, folder_path: str) -> None:
        self._logger.info(f'{self.log_prefix} Re-scheduling watch events handler for path {folder_path}.')
        self.unschedule(self._mapping.get(folder_path).get('watcher'))
        del self._mapping[folder_path]

    def _schedule_watch(self, folder_path: str, identity: Identity, initial_walk: bool = False) -> None:
        self._logger.info(f'{self.log_prefix} Starting to watch folder {folder_path}...')

        event_handler = eventhandler.DataFileHandler(path=folder_path,
                                                     identity=identity,
                                                     tick=self._handler_tick,
                                                     debug=self._debug)

        watcher = self.schedule(event_handler, folder_path, recursive=True)
        self._mapping[folder_path] = {'watcher': watcher, 'handler': event_handler}

        # Perform collect-only quick initial walk in a synchronous way...
        self._start_initial_walk(folder_path, event_handler)

        # ...then launch the upload loop.
        event_handler.launch_restart_loop()

    def _start_initial_walk(self, folder_path, event_handler):
        self._logger.info(f'{self.log_prefix} Starting initial walk inside folder {folder_path}...')

        root_path = Path(folder_path)
        # Just in case we pass a file...
        if root_path.is_file():
            root_path = root_path.parent

        file_count, event_count, ignore_count = 0, 0, 0
        for path in root_path.glob('**/*'):
            # Skipping both hidden files and hidden directories.
            if is_hidden(path) or not path.is_file():
                continue

            file_count += 1
            if Upload.is_finished(str(path)):
                ignore_count += 1
                if ignore_count > 0 and ignore_count % 100 == 0:
                    msg = f'{self.log_prefix} Ignored {ignore_count} uploads already finished in {folder_path}.'
                    self._logger.info(msg)
            else:
                event_count += 1
                # The dispatch of this event will trigger the collect of basic info about the file, and create
                # an entry in the Upload DB. No zip, no upload, no preparation whatsoever. This is handled by
                # the event_handler's "restart_uploads" loop.
                self._logger.info(f'{self.log_prefix} Dispatching file event for {str(path)}.')
                event = FileCreatedEvent(str(path))
                event_handler.dispatch(event)
            time.sleep(0.01)

        if ignore_count < 100:
            self._logger.info(f'{self.log_prefix} Ignored {ignore_count} uploads already finished in {folder_path}.')

        msg = f'{self.log_prefix} Initial walk inside folder {folder_path} '
        msg += f'dispatched {event_count} events for {file_count} files.'
        self._logger.info(msg)

    def forget_folder(self, folder_path: str) -> None:
        if folder_path in self._mapping.keys():
            self._logger.info(f'{self.log_prefix} Forgetting to observe folder {folder_path}')
            self.unschedule(self._mapping[folder_path]['watcher'])
            del self._mapping[folder_path]

    @property
    def observed_paths(self) -> List[str]:
        return list(self._mapping.keys())
