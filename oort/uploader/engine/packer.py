import bz2
import gzip
import os
import pathlib
import warnings
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Optional, Tuple

import dateparser
from astropy.io import fits as pyfits
from astropy.io.fits.verify import VerifyWarning
from astropy.io.votable.exceptions import VOTableSpecWarning
from astropy.utils.exceptions import AstropyWarning

from oort.shared.config import get_oort_logger
from oort.shared.constants import ZIP_EXTENSIONS, get_all_fits_extensions, get_all_xisf_extensions
from oort.shared.identity import Identity
from oort.shared.models import (
    Calibration,
    FINISHED_SUBSTATUSES,
    Observation,
    PREPARATION_DONE_SUBSTATUSES,
    Status,
    Substatus,
    Upload
)
from . import preparator
from . import uploader
from . import zipper

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
    """Class containing the logic to determine the dataset, the night_log and
     the observations/calibrations from filepath."""

    def __init__(self, root_path: str, file_path: str, identity: Identity):
        self._identity = identity
        self._root_path = pathlib.Path(root_path)
        self._raw_file_path = pathlib.Path(file_path)

        self._logger = get_oort_logger('uploader', debug=identity.debug)
        self._parse_type_and_dataset_name()

        # Will work whatever the raw file path extension (zipped or not), and
        # whatever the current state of the two files (exists or not).
        try:
            self._upload = Upload.get(Upload.file_path == self.clear_file_path)
        except Upload.DoesNotExist:
            self._upload = Upload.create(file_path=self.clear_file_path)

        self.update_upload(astronomer=self._identity.username,
                           file_path_zipped=self.zipped_file_path)

        self._find_date_size_and_target_name()

    def do_upload(self):
        if self.should_zip:
            zip = zipper.AsyncZipper(self.clear_file_path)
            zip.start()
            return

        if self.is_hidden_file:
            self._logger.info(f'{self.log_prefix} {self.final_file_name} is an hidden file. Upload skipped.')
            self._archive(Substatus.SKIPPED_HIDDEN_FILE.value)
            return

        if self.is_empty_file:
            self._logger.info(f'{self.log_prefix} {self.final_file_name} is an empty file. Upload skipped.')
            self._archive(Substatus.SKIPPED_EMPTY_FILE.value)
            return

        # Still not 100% satisfactory...

        item = f"{self.final_file_name} ({self._upload.substatus})"
        preparation_succeeded = self._upload.dataset is not None

        if self.should_prepare:
            upload_preparator = preparator.UploadPreparator(self, debug=self._identity.debug)
            preparation_succeeded, _ = upload_preparator.prepare()
        else:
            self._logger.info(f'{self.log_prefix} Preparation already done for {item}.')

        if preparation_succeeded:
            if self.is_already_finished:
                self._logger.info(f'{self.log_prefix} Upload already finished for {item}.')
            else:
                file_uploader = uploader.FileUploader(self)
                file_uploader.upload()

    @property
    def log_prefix(self) -> str:
        return f'[UploadPack: {self.final_file_path}]'

    @property
    def identity(self) -> Identity:
        return self._identity

    @property
    def upload(self) -> Optional[Upload]:
        return self._upload

    @property
    def should_zip(self) -> bool:
        return self.identity.zip and \
               self.is_data_file and \
               self.clear_file_exists and \
               not self.zipped_file_exists and \
               self._upload.substatus != Substatus.ZIPPING.value and \
               os.access(str(self._root_path), os.W_OK)

    @property
    def final_file_path(self):
        if self.should_zip or self.zipped_file_exists:
            return self.zipped_file_path
        return self.clear_file_path

    @property
    def final_file_name(self):
        return pathlib.Path(self.final_file_path).name

    @property
    def has_date_obs(self) -> bool:
        return self._upload.file_date is not None

    @property
    def is_data_file(self) -> bool:
        return ''.join(self._raw_file_path.suffixes).lower() in get_all_fits_extensions() + get_all_xisf_extensions()

    @property
    def clear_file_path(self) -> str:
        return str(self._raw_file_path.with_suffix('')) \
            if self._raw_file_path.suffix in ZIP_EXTENSIONS and len(self._raw_file_path.suffixes) > 1 \
            else str(self._raw_file_path)

    @property
    def zipped_file_path(self) -> str:
        return str(self._raw_file_path) + '.gz' if self._raw_file_path.suffix not in ZIP_EXTENSIONS \
            else str(self._raw_file_path)

    @property
    def clear_file_exists(self) -> bool:
        return pathlib.Path(self.clear_file_path).exists()

    @property
    def zipped_file_exists(self) -> bool:
        return pathlib.Path(self.zipped_file_path).exists()

    @property
    def is_hidden_file(self) -> bool:
        return self._raw_file_path.name[0] == '.'

    @property
    def is_empty_file(self):
        return self._upload.file_size == 0 and self._upload.file_size_zipped == 0

    @property
    def night_log_date_string(self) -> str:
        if not self.has_date_obs:
            return ''
        x = 0 if self._upload.file_date.hour >= 12 else 1
        return (self._upload.file_date - timedelta(days=x)).date().isoformat()

    @property
    def resource_db_class(self):
        return Observation if self._type == ResourceType.OBSERVATION else Calibration

    @property
    def remote_resources_name(self) -> str:
        return self._type.name.lower() + 's'

    @property
    def resource_type(self) -> str:
        return self._type.name.lower()

    @property
    def dataset_name(self) -> str:
        return self._dataset_name.strip()

    @property
    def target_name(self) -> str:
        return self._upload.target_name.strip()

    @property
    def should_prepare(self) -> bool:
        return self._upload.substatus not in PREPARATION_DONE_SUBSTATUSES or self._upload.dataset is None

    @property
    def is_already_finished(self) -> bool:
        return self._upload.status == Status.OK.value and self._upload.substatus in FINISHED_SUBSTATUSES

    def _parse_type_and_dataset_name(self):
        # No starting root, and no ending filename. Just the final folder.
        _clean_path = self._raw_file_path.relative_to(self._root_path).parent
        _is_calib = any([c for c in CALIB_PREFIXES if c in str(_clean_path).lower()])

        self._type = ResourceType.CALIBRATION if _is_calib else ResourceType.OBSERVATION
        self._dataset_name = str(_clean_path)

        if len(self._dataset_name.strip()) == 0 or self._dataset_name.strip() == '.':
            self._dataset_name = f'(folder {self._root_path.name})'

    def _find_date_size_and_target_name(self) -> None:
        _file_date, _target_name = self._find_date_and_target_name()
        _file_size, _zipped_file_size = self._find_sizes()
        self.update_upload(file_date=_file_date,
                           file_size=_file_size,
                           file_size_zipped=_zipped_file_size,
                           target_name=_target_name or '')

    def _find_sizes(self) -> Tuple[float, float]:
        _file_size = 0
        _zipped_file_size = 0
        if self.clear_file_exists:
            _file_size = pathlib.Path(self.clear_file_path).stat().st_size
        if self.zipped_file_exists:
            _zipped_file_size = pathlib.Path(self.zipped_file_path).stat().st_size
        return _file_size, _zipped_file_size

    def _find_date_and_target_name(self) -> Tuple[Optional[datetime], str]:
        _file_date = self._upload.file_date or None
        _target_name = self._upload.target_name or ""
        if _file_date is not None and _target_name != "":
            return _file_date, _target_name

        file_full_extension = ''.join(self._raw_file_path.suffixes).lower()
        file_full_path = str(self._raw_file_path)
        if file_full_extension in get_all_xisf_extensions():
            return self._find_xisf_file_date_and_target_name(file_full_path)
        elif file_full_extension in get_all_fits_extensions():
            return self._find_fits_file_date_and_target_name(file_full_path)
        else:
            return _file_date, _target_name

    def _find_fits_file_date_and_target_name(self, path: str) -> Tuple[Optional[datetime], str]:
        file_date = None
        target_name = ""

        hdulist = None
        try:
            with pyfits.open(path, mode='readonly', memmap=True, ignore_missing_end=True) as hdulist:
                for index, hdu in enumerate(hdulist):
                    # Breaking after 10 HDUs as a workaround to corrupted FITS files that end up in
                    # an infinite loop of HDU reading. Note that relying on len(hdulist) is a BAD
                    # idea as it required to force the reading of all HDUs (lazy loaded by default).
                    if index >= 10:
                        break
                    date_header = hdu.header.get('DATE-OBS') or hdu.header.get('DATE_OBS') or hdu.header.get('DATE')
                    target_name = hdu.header.get('OBJECT', "")  # Make sure to not return None!
                    if date_header is not None:
                        file_date = dateparser.parse(date_header)
                    if file_date and target_name != "":
                        hdulist.close()
                        break
        except Exception as error:
            if hdulist:
                hdulist.close()
            self._logger.debug(f'{self.log_prefix} {str(error)}')

        return file_date, target_name

    def _find_xisf_file_date_and_target_name(self, path: str) -> Tuple[Optional[datetime], str]:
        header = b''
        open_method = open
        file_last_extension = self._raw_file_path.suffix.lower()
        if file_last_extension in ['.gzip', '.gz']:
            open_method = gzip.open
        elif file_last_extension in ['.bzip2', '.bz2']:
            open_method = bz2.open

        with open_method(path, 'rb') as f:
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

        return self._get_xisf_file_date(header), self._get_xisf_target_name(header)

    def _get_xisf_file_date(self, header: bytes) -> Optional[datetime]:
        if len(header) == 0:
            return None
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
            self._logger.debug(f'{self.log_prefix} {str(error)}')
            return None
        else:
            return file_date

    def _get_xisf_target_name(self, header: bytes) -> str:
        if len(header) == 0:
            return ""
        target_name = ""
        prefix = './/{http://www.pixinsight.com/xisf}FITSKeyword'
        try:
            tree = ET.fromstring(header.decode('utf-8'))
            tag = tree.find(prefix + '[@name="OBJECT"]')
            if tag is not None:
                target_name = tag.get('value').strip()
        except Exception as error:
            self._logger.debug(f'{self.log_prefix} {str(error)}')
        return target_name

    def _archive(self, substatus) -> None:
        self.update_upload(status=Status.OK.value, substatus=substatus, ended=datetime.now())

    def update_upload(self, **kwargs) -> None:
        self._upload = self._upload.smart_update(**kwargs)
