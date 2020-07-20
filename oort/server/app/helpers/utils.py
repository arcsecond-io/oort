import datetime
import os
import xml.etree.ElementTree as ET
from configparser import ConfigParser

import dateparser
from astropy.io import fits as pyfits

from .constants import OORT_FILENAME


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


def get_current_date(self):
    before_noon = datetime.datetime.now().hour < 12
    if before_noon:
        return (datetime.datetime.now() - datetime.timedelta(days=1)).date().isoformat()
    else:
        return datetime.datetime.now().date().isoformat()


def get_oort_config(path):
    _config = None
    oort_filepath = os.path.join(path, OORT_FILENAME)
    if os.path.exists(oort_filepath) and os.path.isfile(oort_filepath):
        # Below will fail if the info is missing / wrong.
        _config = ConfigParser()
        with open(oort_filepath, 'r') as f:
            _config.read(oort_filepath)
    return _config


def look_for_telescope_uuid(path):
    config = get_oort_config(path)
    if config and 'telescope' in config:
        return config['telescope']['uuid']
    return None
