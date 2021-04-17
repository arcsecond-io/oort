import gzip
import shutil
import time
from threading import Thread

from oort.shared.config import get_logger
from oort.shared.models import Substatus, Upload


class AsyncZipper(Thread):
    def __init__(self, file_path, debug=False):
        super().__init__()
        self._file_path = file_path
        self._zipped_file_path = file_path + '.gz'
        self._upload, created = Upload.get_or_create(file_path=file_path)
        self._logger = get_logger(debug=debug)

    def run(self):
        self._upload.smart_update(substatus=Substatus.ZIPPING.value)
        self._logger.info(f'Starting to gzip file: {self._file_path}...')
        with open(self._file_path, 'rb') as f_in:
            with gzip.open(self._zipped_file_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        self._upload.smart_update(substatus=Substatus.READY.value)
        self._logger.info(f'Done with gzip of file: {self._file_path}...')
        time.sleep(0.1)
