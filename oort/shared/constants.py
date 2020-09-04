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
