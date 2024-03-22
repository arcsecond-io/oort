from copy import deepcopy
from enum import Enum

OORT_FILENAME = '__oort__'

# We use a custom socket filename because we may need to grep it.
# A custom name ensure we won't confuse our sicket file with another one.
OORT_SUPERVISOR_SOCK_FILENAME = 'oort_supervisor.sock'

# As used in QLFits: https://github.com/onekiloparsec/QLFits
OORT_FITS_EXTENSIONS = [
    '.fits',
    '.fit',
    '.fts',
    '.ft',
    '.mt',
    '.imfits',
    '.imfit',
    '.uvfits',
    '.uvfit',
    '.pha',
    '.rmf',
    '.arf',
    '.rsp',
    '.pi'
]

DATA_EXTENSIONS = OORT_FITS_EXTENSIONS + ['.xisf', ]

ZIP_EXTENSIONS = ['.zip', '.gz', '.bz2']


def _extend_list(extensions):
    for zip in ZIP_EXTENSIONS:
        extensions += [e + zip for e in extensions]
    return extensions


def get_all_xisf_extensions():
    return _extend_list(deepcopy(['.xisf', ]))


def get_all_fits_extensions():
    return _extend_list(deepcopy(OORT_FITS_EXTENSIONS))


class Status(Enum):
    NEW = 'New'
    PREPARING = 'Preparing'
    UPLOADING = 'Uploading'
    OK = 'OK'
    ERROR = 'Error'


class Substatus(Enum):
    PENDING = 'pending'
    ZIPPING = 'zipping...'
    CHECKING = 'checking remote file...'
    READY = 'ready'
    RESTART = 'restart'

    STARTING = 'starting...'
    SYNC_TELESCOPE = 'syncing telescope...'
    SYNC_NIGHTLOG = 'syncing night log...'
    SYNC_OBS_OR_CALIB = 'syncing obs or calib...'
    SYNC_DATASET = 'syncing dataset...'
    UPLOADING = 'uploading...'

    DONE = 'done'
    ERROR = 'error'
    ALREADY_SYNCED = 'already synced'
    IGNORED = 'ignored'
    # --- SKIPPED: MUST BE STARTED WITH THE SAME 'skipped' LOWERCASE WORD. See Context.py ---
    SKIPPED_NO_DATE_OBS = 'skipped (no date obs found)'
    SKIPPED_HIDDEN_FILE = 'skipped (hidden file)'
    SKIPPED_EMPTY_FILE = 'skipped (empty file)'
    # ---


FINISHED_SUBSTATUSES = [Substatus.DONE.value,
                        Substatus.ERROR.value,
                        Substatus.SKIPPED_NO_DATE_OBS.value,
                        Substatus.ALREADY_SYNCED.value]

PREPARATION_DONE_SUBSTATUSES = [Substatus.CHECKING.value,
                                Substatus.READY.value,
                                Substatus.STARTING.value,
                                Substatus.UPLOADING.value] + FINISHED_SUBSTATUSES

ARCSECOND_API_URL_DEV = 'http://localhost:8000'
ARCSECOND_API_URL_PROD = 'https://api.arcsecond.io'

ARCSECOND_WWW_URL_DEV = 'http://localhost:8080'
ARCSECOND_WWW_URL_PROD = 'https://www.arcsecond.io'

API_AUTH_PATH_LOGIN = '/auth/token/'
API_AUTH_PATH_REGISTER = '/auth/registration/'

ECHO_PREFIX = u' • '
ECHO_ERROR_PREFIX = u' • [error] '
