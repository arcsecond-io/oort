import re
from datetime import datetime
from unittest.mock import patch

from oort.uploader.engine.packer import UploadPack
from oort.uploader.engine.utils import get_random_string

root_path = '/Users/onekiloparsec/data/'


def test_packer_calib_bias():
    bias_path = f'/Users/onekiloparsec/data/Biases{get_random_string(5)}/dummy_001.fits'
    with patch.object(UploadPack, '_find_fits_filedate', return_value=datetime.now()), \
         patch.object(UploadPack, '_find_xisf_filedate', return_value=datetime.now()):
        pack = UploadPack(root_path, bias_path)
        assert pack is not None
        # Check detection of FITS or XISF is OK
        assert pack.is_fits_or_xisf is True
        # Check night log date format is OK
        assert re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', pack.night_log_date_string) is not None
        # Check detection of resource is OK
        assert pack.resources_name == 'calibrations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == bias_path.split('/')[-2]


def test_packer_calib_dark():
    bias_path = f'/Users/onekiloparsec/data/dArkss{get_random_string(5)}/dummy_001.fits'
    with patch.object(UploadPack, '_find_fits_filedate', return_value=datetime.now()), \
         patch.object(UploadPack, '_find_xisf_filedate', return_value=datetime.now()):
        pack = UploadPack(root_path, bias_path)
        assert pack is not None
        # Check detection of FITS or XISF is OK
        assert pack.is_fits_or_xisf is True
        # Check night log date format is OK
        assert re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', pack.night_log_date_string) is not None
        # Check detection of resource is OK
        assert pack.resources_name == 'calibrations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == bias_path.split('/')[-2]


def test_packer_calibs_flat_no_filter():
    bias_path = f'/Users/onekiloparsec/data/FLATS{get_random_string(5)}/dummy_001.fits'
    with patch.object(UploadPack, '_find_fits_filedate', return_value=datetime.now()), \
         patch.object(UploadPack, '_find_xisf_filedate', return_value=datetime.now()):
        pack = UploadPack(root_path, bias_path)
        assert pack is not None
        # Check detection of FITS or XISF is OK
        assert pack.is_fits_or_xisf is True
        # Check night log date format is OK
        assert re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', pack.night_log_date_string) is not None
        # Check detection of resource is OK
        assert pack.resources_name == 'calibrations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == bias_path.split('/')[-2]


def test_packer_calibs_flat_with_filter():
    bias_path = f'/Users/onekiloparsec/data/FLATS{get_random_string(5)}/U/dummy_001.fits'
    with patch.object(UploadPack, '_find_fits_filedate', return_value=datetime.now()), \
         patch.object(UploadPack, '_find_xisf_filedate', return_value=datetime.now()):
        pack = UploadPack(root_path, bias_path)
        assert pack is not None
        # Check detection of FITS or XISF is OK
        assert pack.is_fits_or_xisf is True
        # Check night log date format is OK
        assert re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', pack.night_log_date_string) is not None
        # Check detection of resource is OK
        assert pack.resources_name == 'calibrations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == bias_path.split('/')[-3] + ' ' + bias_path.split('/')[-2]
