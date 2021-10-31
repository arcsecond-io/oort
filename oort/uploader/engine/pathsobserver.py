import time
from pathlib import Path
from threading import Thread, Timer
from typing import List

from watchdog.events import FileCreatedEvent
from watchdog.observers import Observer

from oort.shared.config import get_oort_config_upload_folder_sections, get_oort_logger
from oort.shared.constants import OORT_UPLOADER_FOLDER_DETECTION_TICK_SECONDS
from oort.shared.identity import Identity
from oort.shared.models import Upload
from oort.shared.utils import is_hidden
from . import eventhandler


class PathObserver(Observer):
    def __init__(self, folder: str, identity: Identity, debug=False):
        super().__init__()

        self._folder_path = Path(folder)
        # Just in case we pass a file...
        if self._folder_path.is_file():
            self._folder_path = self._folder_path.parent

        self._identity = identity
        self._debug = debug
        self._handler_tick = 20.0
        self._logger = get_oort_logger('uploader', debug=self._debug)

        self._watcher = None
        self._event_handler = eventhandler.DataFileHandler(path=self._folder_path,
                                                           identity=self._identity,
                                                           tick=self._handler_tick,
                                                           debug=self._debug)

    @property
    def debug(self):
        return self._debug

    @property
    def log_prefix(self) -> str:
        return f"[PathsObserver {str(self._folder_path)}]"

    def prepare(self) -> None:
        self._logger.info(f'{self.log_prefix} Starting initial walk...')

        file_count, event_count, ignore_count = 0, 0, 0
        for path in self._folder_path.glob('**/*'):
            # Skipping both hidden files and hidden directories.
            if is_hidden(path) or not path.is_file():
                continue

            file_count += 1
            if Upload.is_finished(str(path)):
                ignore_count += 1
                if ignore_count > 0 and ignore_count % 100 == 0:
                    msg = f'{self.log_prefix} Ignored {ignore_count} uploads already finished.'
                    self._logger.info(msg)
            else:
                event_count += 1
                # The dispatch of this event will trigger the collect of basic info about the file, and create
                # an entry in the Upload DB. No zip, no upload, no preparation whatsoever. This is handled by
                # the event_handler's "restart_uploads" loop.
                self._logger.info(f'{self.log_prefix} Dispatching file event for {str(path)}.')
                event = FileCreatedEvent(str(path))
                self._event_handler.dispatch(event)
            time.sleep(0.01)

        if ignore_count < 100:
            self._logger.info(f"{self.log_prefix} Ignored {ignore_count} uploads already finished.")

        msg = f"{self.log_prefix} Initial walk dispatched {event_count} events for {file_count} files."
        self._logger.info(msg)

    def schedule_and_start(self) -> None:
        if self._watcher is None:
            self._watcher = self.schedule(self._event_handler, str(self._folder_path), recursive=True)
            self._event_handler.launch_restart_loop()
        if not self.is_alive():
            self.start()

    def unschedule_watch(self) -> None:
        self._logger.info(f'{self.log_prefix} Un-scheduling watch events handler.')
        self.unschedule(self._watcher)


class PathObserverManager(Thread):
    def __init__(self, debug=False):
        super().__init__()
        self._mapping = {}
        self._debug = debug
        self._logger = get_oort_logger('uploader', debug=self._debug)
        Timer(1, self._detect_watched_folders).start()

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value
        self._logger = get_oort_logger('uploader', debug=self._debug)
        for folder_path in self._mapping.keys():
            self._mapping[folder_path].debug = self._debug

    @property
    def log_prefix(self) -> str:
        return '[PathsObserver]'

    @property
    def observed_paths(self) -> List[str]:
        return list(self._mapping.keys())

    def start(self) -> None:
        # Every OORT_UPLOADER_FOLDER_DETECTION_TICK_SECONDS seconds, new folders are being checked.
        Timer(OORT_UPLOADER_FOLDER_DETECTION_TICK_SECONDS, self._detect_watched_folders).start()
        super().start()

    def _detect_watched_folders(self):
        self._logger.info(f'{self.log_prefix} Detecting watched folder paths...')

        mapping_keys = self._mapping.keys()
        folder_sections = get_oort_config_upload_folder_sections()
        self._logger.info(f"{self.log_prefix} Found {len(folder_sections)} folders...")

        # Unschedule all paths that are not observed anymore.
        folder_section_paths = [section.get('path') for section in folder_sections]
        for mapping_key in mapping_keys:
            if mapping_key not in folder_section_paths:
                observer = self._mapping[mapping_key]
                observer.unschedule_watch()

        # Re-read mapping keys
        mapping_keys = self._mapping.keys()
        # Now, schedule, if not yet done, all folders to be watched.
        for folder_section in folder_sections:
            folder_path = folder_section.get('path')
            identity = Identity.from_folder_section(folder_section)

            if folder_path not in mapping_keys:
                observer = PathObserver(folder_path, identity, self._debug)
                self._mapping[folder_path] = observer
                observer.prepare()
                observer.schedule_and_start()

    def stop_observers(self):
        for observer in self._mapping.values():
            observer.stop()
