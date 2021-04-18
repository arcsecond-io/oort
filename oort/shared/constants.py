from copy import deepcopy

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
