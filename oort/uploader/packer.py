import pathlib
import warnings
from datetime import timedelta
from enum import auto

from astropy.io.fits.verify import VerifyWarning
from astropy.io.votable.exceptions import VOTableSpecWarning
from astropy.utils.exceptions import AstropyWarning

from oort.common.config import get_oort_logger
from oort.common.constants import *
from oort.common.identity import Identity
from .preparator import UploadPreparator
from .uploader import FileUploader

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

    def __init__(self, root_path: str, file_path: str, identity: Identity, force: bool = False):
        self._identity = identity
        self._root_path = pathlib.Path(root_path)
        self._raw_file_path = pathlib.Path(file_path)
        self._force = force
        self._logger = get_oort_logger('uploader', debug=identity.api == 'dev')
        self._parse_type_and_folder_name()

    def collect_file_info(self):
        self._logger.info(f'{self.log_prefix} {self.final_file_name} Collecting info...')
        self._find_date_size_and_target_name()

    def prepare_and_upload_file(self, display_progress: bool = False):
        if self.is_hidden_file:
            self._logger.info(f'{self.log_prefix} {self.final_file_name} is an hidden file. Upload skipped.')

        elif self.is_empty_file:
            self._logger.info(f'{self.log_prefix} {self.final_file_name} is an empty file. Upload skipped.')

        else:
            item = f"{self.final_file_name} ({self._upload.substatus})"
            if self.is_already_prepared:
                self._logger.info(f'{self.log_prefix} Preparation already done for {item}.')
                preparation_succeeded = True
            else:
                upload_preparator = UploadPreparator(self, debug=self._identity.api == 'dev')
                preparation_succeeded = upload_preparator.prepare()

            if preparation_succeeded:
                if self.is_already_finished:
                    self._logger.info(f'{self.log_prefix} Upload already finished for {item}.')
                else:
                    file_uploader = FileUploader(self, display_progress)
                    file_uploader.upload_file()

    @property
    def log_prefix(self) -> str:
        return f'[UploadPack: {self.final_file_path}]'

    @property
    def identity(self) -> Identity:
        return self._identity

    @property
    def final_file_path(self):
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
    def clear_file_exists(self) -> bool:
        return pathlib.Path(self.clear_file_path).exists()

    @property
    def is_hidden_file(self) -> bool:
        return self._raw_file_path.name[0] == '.'

    @property
    def is_empty_file(self):
        return self._find_sizes() == (0, 0)

    @property
    def night_log_date_string(self) -> str:
        if not self.has_date_obs:
            return ''
        x = 0 if self._upload.file_date.hour >= 12 else 1
        return (self._upload.file_date - timedelta(days=x)).date().isoformat()

    # @property
    # def resource_db_class(self):
    #     return Observation if self._type == ResourceType.OBSERVATION else Calibration

    @property
    def remote_resources_name(self) -> str:
        return self._type.name.lower() + 's'

    @property
    def resource_type(self) -> str:
        return self._type.name.lower()

    @property
    def clean_folder_name(self) -> str:
        return self._clean_folder_name.strip()

    @property
    def root_folder_name(self) -> str:
        return str(self._root_path)

    @property
    def target_name(self) -> str:
        return self._upload.target_name.strip()

    @property
    def is_already_prepared(self) -> bool:
        return self._upload.substatus in PREPARATION_DONE_SUBSTATUSES or self._upload.dataset is not None

    @property
    def is_already_finished(self) -> bool:
        return self._upload.status == Status.OK.value and self._upload.substatus in FINISHED_SUBSTATUSES

    def _parse_type_and_folder_name(self):
        # No ending filename. Just the final folder, including the root one! --------vvvvvv
        self._clean_folder_name = str(self._raw_file_path.relative_to(self._root_path.parent).parent)
        _is_calib = any([c for c in CALIB_PREFIXES if c in self._clean_folder_name.lower()])
        self._type = ResourceType.CALIBRATION if _is_calib else ResourceType.OBSERVATION

    def _find_date_size_and_target_name(self) -> None:
        _file_date, _target_name = self._find_date_and_target_name()
        _file_size = self._find_size()

    def _find_size(self) -> float:
        _file_size = 0
        if self.clear_file_exists:
            _file_size = pathlib.Path(self.clear_file_path).stat().st_size
        return _file_size
