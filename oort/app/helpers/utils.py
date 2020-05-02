# from configparser import ConfigParser, DuplicateOptionError
import dateparser
from astropy.io import fits as pyfits


def find_first_in_list(objects, **kwargs):
    return next((obj for obj in objects if
                 len(set(obj.keys()).intersection(kwargs.keys())) > 0 and
                 all([obj[k] == v for k, v in kwargs.items() if k in obj.keys()])),
                None)


class SafeDict(dict):
    def __init__(self, *args):
        dict.__init__(self, args)

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            return None

    def append(self, key, *items):
        if key not in self.keys():
            self[key] = []
        for item in items:
            if item not in self[key]:
                self[key].append(item)


def find_fits_filedate(path, debug):
    file_date = None
    try:
        hdulist = pyfits.open(path)
    except Exception as error:
        if debug: print(str(error))
    else:
        for hdu in hdulist:
            date_header = hdu.header.get('DATE') or hdu.header.get('DATE-OBS')
            if not date_header:
                continue
            file_date = dateparser.parse(date_header)
            if file_date:
                break
        hdulist.close()
    return file_date


