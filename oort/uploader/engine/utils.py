import datetime
import xml.etree.ElementTree as ET

import dateparser
from astropy.io import fits as pyfits


def get_current_date(self):
    before_noon = datetime.datetime.now().hour < 12
    if before_noon:
        return (datetime.datetime.now() - datetime.timedelta(days=1)).date().isoformat()
    else:
        return datetime.datetime.now().date().isoformat()


def find_fits_filedate(path):
    file_date = None
    try:
        hdulist = pyfits.open(path)
    except Exception as error:
        print(str(error))
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


def find_xisf_filedate(path):
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
            print(str(error))
            return None
        else:
            return file_date
