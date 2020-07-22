import os
from enum import Enum

from oort.uploader.engine.utils import find_fits_filedate, find_xisf_filedate

CALIB_PREFIXES = ['bias', 'dark', 'flats']


class FamilyType(Enum):
    OBSERVATION = 1
    CALIBRATION = 2


class UploadPack(object):
    def __init__(self, root_path, file_path):
        self._root_path = root_path
        self._file_path = file_path

        self._filedate = find_fits_filedate(self._file_path) or find_xisf_filedate(self._file_path)

        self._segments = self._file_path[len(self._root_path):].split(os.sep)
        self._filename = self._segments.pop()

        self._type = FamilyType.OBSERVATION
        self._filter_name = None

        for i in range(2):
            if any([c for c in CALIB_PREFIXES if c in self._segments[-i - 1].lower()]):
                self._type = FamilyType.CALIBRATION
                if i == 1:
                    self._filter_name = self._segments[-1]
                break

    @property
    def is_fits_or_xisf(self):
        return self._filedate is not None
