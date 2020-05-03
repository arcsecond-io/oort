import logging
import dateparser
import xml.etree.ElementTree as ET

from astropy.io import fits as pyfits
from .constants import *


def find_first_in_list(objects, **kwargs):
    return next((obj for obj in objects if
                 len(set(obj.keys()).intersection(kwargs.keys())) > 0 and
                 all([obj[k] == v for k, v in kwargs.items() if k in obj.keys()])),
                None)


def get_oort_logger():
    logger = logging.getLogger(OORT_APPNAME)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(OORT_UPLOADS_LOG_FILENAME)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


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


def find_xisf_filedate(path, debug):
    file_date = None
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
        try:
            tree = ET.fromstring(header.decode('utf-8'))
            tag = tree.find('.//{http://www.pixinsight.com/xisf}FITSKeyword[@name="DATE-OBS"]')
            if tag is None:
                tag = tree.find('.//{http://www.pixinsight.com/xisf}FITSKeyword[@name="DATE"]')
            if tag is not None:
                file_date = dateparser.parse(tag.get('value'))
        except Exception as error:
            if debug: print(str(error))
            return None
        else:
            return file_date
