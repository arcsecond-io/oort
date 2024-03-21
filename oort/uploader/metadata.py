import bz2
import gzip
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional, Tuple

import dateparser
from astropy.io import fits as pyfits

from oort.common.constants import get_all_xisf_extensions, get_all_fits_extensions


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
