import os
import threading
import time

from watchdog.events import FileSystemEventHandler

from oort.cli.folders import check_organisation
from oort.shared.config import get_logger
from oort.shared.identity import Identity
from . import packer


def perform_initial_walk(root_path: str, identity: Identity, debug: bool):
    logger = get_logger(debug=debug)
    logger.info(f'Running initial walk for {root_path}')

    time.sleep(0.5)

    if identity.subdomain:
        check_organisation(identity.subdomain, debug)

    time.sleep(0.5)

    initial_packs = []
    for root, _, filenames in os.walk(root_path):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            if os.path.isfile(file_path) and not os.path.basename(file_path).startswith('.'):
                initial_packs.append(packer.UploadPack(root_path, file_path, identity))

    time.sleep(0.5)

    for pack in initial_packs:
        pack.do_upload()

    logger.info(f'Finished initial walk for {root_path}')


class DataFileHandler(FileSystemEventHandler):
    def __init__(self, path: str, identity: Identity, debug=False):
        super().__init__()
        self._root_path = path
        self._identity = identity
        self._debug = debug
        self._logger = get_logger(debug=self._debug)
        self._walk_process = None

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value
        self._logger = get_logger(debug=self._debug)

    def run_initial_walk(self):
        if self._walk_process is None:
            self._walk_process = threading.Thread(target=perform_initial_walk,
                                                  args=(self._root_path, self._identity, self._debug))
        if not self._walk_process.is_alive():
            self._walk_process.start()

    def on_created(self, event):
        if os.path.isfile(event.src_path) and not os.path.basename(event.src_path).startswith('.'):
            self._logger.info(f'Created event for path : {event.src_path}')

            file_size = -1
            while file_size != os.path.getsize(event.src_path):
                file_size = os.path.getsize(event.src_path)
                time.sleep(0.1)

            pack = packer.UploadPack(self._root_path, event.src_path, self._identity)
            pack.do_upload()

    def on_moved(self, event):
        self._logger.info(f'{event.event_type}: {event.src_path}')

    def on_deleted(self, event):
        self._logger.info(f'{event.event_type}: {event.src_path}')

    def on_modified(self, event):
        self._logger.info(f'{event.event_type}: {event.src_path}')
