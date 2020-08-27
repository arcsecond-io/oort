import os
import threading
import time

from watchdog.events import FileSystemEventHandler

from oort.cli.folders import check_organisation
from oort.shared.config import get_logger
from oort.shared.identity import Identity
from .packer import UploadPack
from .preparator import UploadPreparator
from .uploader import FileUploader


class DataFileHandler(FileSystemEventHandler):
    def __init__(self, path: str, identity: Identity, debug=False):
        super().__init__()
        self._root_path = path
        self._identity = identity
        self._debug = debug
        self._logger = get_logger(debug=self._debug)
        self._initial_packs = []
        self._thread = None

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value
        self._logger = get_logger(debug=self._debug)

    def run_initial_walk(self):
        if self._thread is None:
            self._thread = threading.Thread(target=self._perform_initial_walk)
        if self._thread.is_alive() is False:
            self._thread.start()

    def _perform_initial_walk(self):
        self._logger.info(f'Running initial walk for {self._root_path}')
        time.sleep(0.5)
        if self._identity.organisation:
            check_organisation(self._identity.organisation, self._identity.debug)
        time.sleep(0.5)
        self._prepare_initial_packs()
        time.sleep(0.5)
        self._dispatch_valid_packs()
        self._logger.info(f'Finished initial walk for {self._root_path}')

    def _prepare_initial_packs(self):
        for root, _, filenames in os.walk(self._root_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if os.path.isfile(file_path) and not os.path.basename(file_path).startswith('.'):
                    self._initial_packs.append(UploadPack(self._root_path, file_path, self._identity))

    def _dispatch_valid_packs(self):
        for pack in self._initial_packs:
            if pack.is_fits_or_xisf:
                self._perform_upload(pack)
            else:
                self._logger.info(f'{pack.file_path} not a FITS or XISF. Skipping.')
                pack.archive()

    def _perform_upload(self, pack):
        preparator = UploadPreparator(pack=pack, identity=self._identity, debug=self._debug)
        preparator.prepare()
        if preparator.dataset:
            file_uploader = FileUploader(preparator.pack, preparator.identity, preparator.dataset)
            file_uploader.upload()
        else:
            self._logger.info(f'Missing dataset, upload skipped for {preparator.pack.file_path}')

    def on_created(self, event):
        if os.path.isfile(event.src_path) and not os.path.basename(event.src_path).startswith('.'):
            self._logger.info(f'Created event for path : {event.src_path}')

            file_size = -1
            while file_size != os.path.getsize(event.src_path):
                file_size = os.path.getsize(event.src_path)
                time.sleep(0.1)

            pack = UploadPack(self._root_path, event.src_path, self._identity)
            self._perform_upload(pack)

    def on_moved(self, event):
        self._logger.info(f'{event.event_type}: {event.src_path}')

    def on_deleted(self, event):
        self._logger.info(f'{event.event_type}: {event.src_path}')

    def on_modified(self, event):
        self._logger.info(f'{event.event_type}: {event.src_path}')
