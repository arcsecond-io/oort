import os
import warnings
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Optional

import dateparser
from astropy.io import fits as pyfits
from astropy.io.fits.verify import VerifyWarning
from astropy.io.votable.exceptions import VOTableSpecWarning
from astropy.utils.exceptions import AstropyWarning

from oort.shared.config import get_logger
from oort.shared.identity import Identity
from oort.shared.models import (Calibration, FINISHED_SUBSTATUSES, Observation, PREPARATION_DONE_SUBSTATUSES, Status,
                                Upload)

warnings.simplefilter('ignore', category=AstropyWarning)
warnings.simplefilter('ignore', category=VOTableSpecWarning)
warnings.simplefilter('ignore', category=VerifyWarning)

CALIB_PREFIXES = ['bias', 'dark', 'flats', 'calib']


class ResourceType(Enum):
    OBSERVATION = auto()
    CALIBRATION = auto()


class CalibrationType(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.lower().capitalize()

    def entitle(self, suffix=''):
        if self is CalibrationType.FLATS:
            assert (len(suffix) > 0)
            suffix = ' ' + suffix
        return f'{self.name}{suffix}'

    BIASES = auto()
    DARKS = auto()
    FLATS = auto()


class UploadPack(object):
    """Logic to determine dataset, night_log and observations/calibrations from filepath."""

    def __init__(self, root_path, file_path, identity: Identity):
        self._logger = get_logger(debug=True)

        self._root_path = root_path
        self._file_path = file_path

        self._identity = identity
        self._upload = None

        self._parse()

        self._upload, created = Upload.get_or_create(file_path=self.file_path)
        if created:
            self._find_date_and_size()
        else:
            self._file_date = self._upload.file_date
            self._file_size = self._upload.file_size

    def _parse(self):
        self._segments = [s for s in self._file_path[len(self._root_path):].split(os.sep) if s != '']
        self._filename = self._segments.pop()

        self._type = ResourceType.OBSERVATION
        self._dataset_name = None

        for i in range(1, min(len(self._segments), 2) + 1):
            if any([c for c in CALIB_PREFIXES if c in self._segments[-i].lower()]):
                self._type = ResourceType.CALIBRATION
                if i == 1:
                    self._dataset_name = self._segments[-i]
                else:  # i = 2
                    self._dataset_name = f'{self._segments[-i]}/{self._segments[-1]}'
                break

        if self._type == ResourceType.OBSERVATION:
            self._dataset_name = '/'.join(self._segments)

        if len(self._dataset_name.strip()) == 0:
            self._dataset_name = f'(folder {os.path.basename(self._root_path)})'

        # What happens when rules change: dataset will change -> new upload...

    def _find_date_and_size(self):
        self._file_date = self._find_date(self._file_path)
        self._file_size = os.path.getsize(self._file_path)
        self._upload.smart_update(file_date=self.file_date, file_size=self.file_size)

    def archive(self, substatus):
        assert substatus is not None
        self._upload.smart_update(status=Status.OK.value, substatus=substatus)

    @property
    def identity(self) -> Identity:
        return self._identity

    @property
    def upload(self) -> Optional[Upload]:
        return self._upload

    @property
    def file_path(self) -> str:
        return self._file_path

    @property
    def file_date(self) -> Optional[datetime]:
        return self._file_date

    @property
    def file_name(self) -> str:
        return os.sep.join(self._segments)

    @property
    def file_size(self) -> int:
        return self._file_size

    @property
    def is_fits_or_xisf(self) -> bool:
        return self._file_date is not None

    @property
    def night_log_date_string(self) -> str:
        if not self.is_fits_or_xisf:
            return ''
        x = 0 if self._file_date.hour >= 12 else 1
        return (self._file_date - timedelta(days=x)).date().isoformat()

    @property
    def resource_type(self) -> str:
        return self._type.name.lower()

    @property
    def resource_db_class(self):
        return Observation if self._type == ResourceType.OBSERVATION else Calibration

    @property
    def remote_resources_name(self) -> str:
        return self._type.name.lower() + 's'

    @property
    def dataset_name(self) -> str:
        return self._dataset_name.strip()

    @property
    def should_prepare(self) -> bool:
        return self._upload.substatus not in PREPARATION_DONE_SUBSTATUSES

    @property
    def is_already_finished(self) -> bool:
        return self._upload.substatus in FINISHED_SUBSTATUSES

    def _find_date(self, path):
        _, extension = os.path.splitext(path)
        if extension.lower() == '.xisf':
            return self._find_xisf_filedate(path)
        else:
            return self._find_fits_filedate(path)

    def _find_fits_filedate(self, path):
        file_date = None
        try:
            with pyfits.open(path) as hdulist:
                for hdu in hdulist:
                    date_header = hdu.header.get('DATE') or hdu.header.get('DATE-OBS') or hdu.header.get('DATE_OBS')
                    if not date_header:
                        continue
                    file_date = dateparser.parse(date_header)
                    if file_date:
                        break
        except Exception as error:
            self._logger.debug(str(error))
        return file_date

    def _find_xisf_filedate(self, path):
        header = b''
        with open(path, 'rb') as f:
            bytes = b''
            while b'</xisf>' not in bytes:
                bytes = f.read(500)
                if header == b'' and b'<xisf' not in bytes:
                    # If '<xisf' is not in the first 500 bytes, it's not a xisf
                    break
                elif header == b'' and b'<xisf' in bytes:
                    index = bytes.find(b'<xisf')
                    header += bytes[index:]
                elif b'</xisf>' in bytes:
                    index = bytes.find(b'</xisf>')
                    header += bytes[:index] + b'</xisf>'
                elif len(header) > 0:
                    header += bytes
        if len(header) > 0:
            return self._get_xisf_filedate(header)

    def _get_xisf_filedate(self, header):
        file_date = None
        prefix = './/{http://www.pixinsight.com/xisf}FITSKeyword'
        try:
            tree = ET.fromstring(header.decode('utf-8'))
            tag = tree.find(prefix + '[@name="DATE-OBS"]')
            if tag is None:
                tag = tree.find(prefix + '[@name="DATE_OBS"]')
            if tag is None:
                tag = tree.find(prefix + '[@name="DATE"]')
            if tag is not None:
                file_date = dateparser.parse(tag.get('value'))
        except Exception as error:
            self._logger.debug(str(error))
            return None
        else:
            return file_date
