import gzip
import os
import pathlib
import shutil
import sys
import time
from stat import S_IREAD, S_IRGRP, S_IROTH, S_IWUSR
from threading import Event, Thread

from oort.shared.config import get_logger
from oort.shared.models import Substatus, Upload

zipper_stop_event = Event()


class AsyncZipper(Thread):
    def __init__(self, file_path, debug=False):
        super().__init__()
        self._debug = debug
        self._file_path = file_path
        self._zipped_file_path = file_path + '.gz'
        self._upload, created = Upload.get_or_create(file_path=file_path)
        self._initial_substatus = self._upload.substatus
        self._logger = get_logger(debug=debug)

    @property
    def log_prefix(self) -> str:
        return '[AsyncZipper: ' + '/'.join(self._file_path.split(os.sep)[-2:]) + ']'

    def run(self):
        self._upload.smart_update(substatus=Substatus.ZIPPING.value)
        self._logger.info(f'{self.log_prefix} Starting to gzip file: {self._file_path}...')
        # Make file read-only to avoid deletion until end
        os.chmod(self._file_path, S_IREAD | S_IRGRP | S_IROTH)
        try:
            with open(self._file_path, 'rb') as f_in:
                with gzip.open(self._zipped_file_path, 'wb') as f_out:
                    if zipper_stop_event.is_set():
                        raise Exception('Zipper stop Event is set.')
                    else:
                        shutil.copyfileobj(f_in, f_out)
                        if self._debug:  # used for manually testing
                            time.sleep(10)

        except Exception as e:
            self._upload.smart_update(substatus=self._initial_substatus)
            pathlib.Path(self._zipped_file_path).unlink(missing_ok=True)
            self._logger.error(f'{self.log_prefix} [{str(e)}] Cancelling gzip of file: {self._file_path}.')

        else:
            # Make zipped file read-only
            os.chmod(self._zipped_file_path, S_IREAD | S_IRGRP | S_IROTH)
            # Makes original file read-write for the owner
            os.chmod(self._file_path, S_IWUSR | S_IREAD)
            # Deleting original file
            pathlib.Path(self._file_path).unlink()
            # Back to upload pending status.
            self._upload.smart_update(substatus=Substatus.PENDING.value)
            self._logger.info(f'{self.log_prefix} Done with gzip of file: {self._file_path}...')
            time.sleep(0.1)


if __name__ == '__main__':
    zip = AsyncZipper(sys.argv[1], debug=True)
    zip.start()
    zip.join(20)
