import os
import xml.etree.ElementTree as ET
from datetime import timedelta
from enum import Enum, auto

import dateparser
from astropy.io import fits as pyfits

from oort.shared.models import Calibration, Dataset, DoesNotExist, Observation, Upload

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

    def __init__(self, root_path, file_path, longitude=None):
        self._root_path = root_path
        self._file_path = file_path
        self._longitude = longitude
        self._upload = None
        self._pack()

    def _pack(self):
        self._file_date = self._find_fits_filedate(self._file_path) or self._find_xisf_filedate(self._file_path)
        self._file_size = os.path.getsize(self._file_path)

        self._segments = self._file_path[len(self._root_path):].split(os.sep)
        self._filename = self._segments.pop()

        self._type = ResourceType.OBSERVATION
        self._dataset_name = None

        for i in range(1, min(len(self._segments), 2) + 1):
            if any([c for c in CALIB_PREFIXES if c in self._segments[-i].lower()]):
                self._type = ResourceType.CALIBRATION
                if i == 1:
                    self._dataset_name = self._segments[-i]
                else:  # i = 2
                    self._dataset_name = f'{self._segments[-i]} {self._segments[-1]}'
                break

        if self._type == ResourceType.OBSERVATION:
            self._dataset_name = ' '.join(self._segments)

        if len(self._dataset_name.strip()) == 0:
            self._dataset_name = f'(folder {os.path.basename(self._root_path)})'

        try:
            self._upload = Upload.get(file_path=self.file_path)
        except DoesNotExist:
            self._upload = Upload.create(file_path=self.file_path)

        self._upload.file_date = self.file_date
        self._upload.file_size = self.file_size
        self._upload.save()

    @property
    def file_path(self):
        return self._file_path

    @property
    def file_date(self):
        return self._file_date

    @property
    def file_name(self):
        return os.sep.join(self._segments)

    @property
    def file_size(self):
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
    def resource_type(self):
        return self._type.name.lower()

    @property
    def resource_db_class(self):
        return Observation if self._type == ResourceType.OBSERVATION else Calibration

    @property
    def remote_resources_name(self):
        return self._type.name.lower() + 's'

    @property
    def dataset_name(self):
        return self._dataset_name

    def _find_fits_filedate(self, path):
        file_date = None
        try:
            hdulist = pyfits.open(path)
        except Exception as error:
            print(str(error))
        else:
            for hdu in hdulist:
                date_header = hdu.header.get('DATE') or hdu.header.get('DATE-OBS') or hdu.header.get('DATE_OBS')
                if not date_header:
                    continue
                file_date = dateparser.parse(date_header)
                if file_date:
                    break
            hdulist.close()
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
        try:
            tree = ET.fromstring(header.decode('utf-8'))
            tag = tree.find('.//{http://www.pixinsight.com/xisf}FITSKeyword[@name="DATE-OBS"]')
            if tag is None:
                tag = tree.find('.//{http://www.pixinsight.com/xisf}FITSKeyword[@name="DATE"]')
            if tag is not None:
                file_date = dateparser.parse(tag.get('value'))
        except Exception as error:
            print(str(error))
            return None
        else:
            return file_date

    def save(self, **kwargs):
        if 'dataset' in kwargs.keys():
            dataset_uuid = kwargs.pop('dataset')
            try:
                dataset = Dataset.get(uuid=dataset_uuid)
            except DoesNotExist:
                # really?
                pass
            else:
                self._upload.dataset = dataset

        for k, v in kwargs.items():
            setattr(self._upload, k, v)

        self._upload.save()
