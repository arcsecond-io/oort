import re
import uuid
from datetime import datetime
from unittest.mock import patch

from oort.shared.identity import Identity
from oort.shared.utils import get_random_string
from oort.uploader.engine.packer import UploadPack
from tests.utils import use_test_database

root_path = '/Users/onekiloparsec/data/'

telescope_uuid = '44f5bee9-a557-4264-86d6-c877d5013788'
identity = Identity('cedric', str(uuid.uuid4()), 'saao', 'admin', telescope_uuid)


@use_test_database
def test_packer_calib_bias():
    path = f'/Users/onekiloparsec/data/Biases{get_random_string(5)}/dummy_001.fits'
    with patch('os.path.getsize', return_value=10), \
         patch.object(UploadPack, '_find_fits_filedate', return_value=datetime.now()), \
         patch.object(UploadPack, '_find_xisf_filedate', return_value=datetime.now()):
        pack = UploadPack(root_path, path, identity)
        assert pack is not None
        # Check detection of FITS or XISF is OK
        assert pack.is_fits_or_xisf is True
        # Check night log date format is OK
        assert re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', pack.night_log_date_string) is not None
        # Check detection of resource is OK
        assert pack.resource_type == 'calibration'
        assert pack.remote_resources_name == 'calibrations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == path.split('/')[-2]


@use_test_database
def test_packer_calib_dark():
    path = f'/Users/onekiloparsec/data/dArkss{get_random_string(5)}/dummy_001.fits'
    with patch('os.path.getsize', return_value=10), \
         patch.object(UploadPack, '_find_fits_filedate', return_value=datetime.now()), \
         patch.object(UploadPack, '_find_xisf_filedate', return_value=datetime.now()):
        pack = UploadPack(root_path, path, identity)
        assert pack is not None
        # Check detection of FITS or XISF is OK
        assert pack.is_fits_or_xisf is True
        # Check night log date format is OK
        assert re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', pack.night_log_date_string) is not None
        # Check detection of resource is OK
        assert pack.resource_type == 'calibration'
        assert pack.remote_resources_name == 'calibrations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == path.split('/')[-2]


@use_test_database
def test_packer_calibs_flat_no_filter():
    path = f'/Users/onekiloparsec/data/FLATS{get_random_string(5)}/dummy_001.fits'
    with patch('os.path.getsize', return_value=10), \
         patch.object(UploadPack, '_find_fits_filedate', return_value=datetime.now()), \
         patch.object(UploadPack, '_find_xisf_filedate', return_value=datetime.now()):
        pack = UploadPack(root_path, path, identity)
        assert pack is not None
        # Check detection of FITS or XISF is OK
        assert pack.is_fits_or_xisf is True
        # Check night log date format is OK
        assert re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', pack.night_log_date_string) is not None
        # Check detection of resource is OK
        assert pack.resource_type == 'calibration'
        assert pack.remote_resources_name == 'calibrations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == path.split('/')[-2]


@use_test_database
def test_packer_calibs_flat_with_filter():
    path = f'/Users/onekiloparsec/data/FLATS{get_random_string(5)}/U/dummy_001.fits'
    with patch('os.path.getsize', return_value=10), \
         patch.object(UploadPack, '_find_fits_filedate', return_value=datetime.now()), \
         patch.object(UploadPack, '_find_xisf_filedate', return_value=datetime.now()):
        pack = UploadPack(root_path, path, identity)
        assert pack is not None
        # Check detection of FITS or XISF is OK
        assert pack.is_fits_or_xisf is True
        # Check night log date format is OK
        assert re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', pack.night_log_date_string) is not None
        # Check detection of resource is OK
        assert pack.resource_type == 'calibration'
        assert pack.remote_resources_name == 'calibrations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == path.split('/')[-3] + '/' + path.split('/')[-2]


@use_test_database
def test_packer_observation_no_filter():
    path = '/Users/onekiloparsec/data/HD5980/dummy_010.fits'
    with patch('os.path.getsize', return_value=10), \
         patch.object(UploadPack, '_find_fits_filedate', return_value=datetime.now()), \
         patch.object(UploadPack, '_find_xisf_filedate', return_value=datetime.now()):
        pack = UploadPack(root_path, path, identity)
        assert pack is not None
        # Check detection of FITS or XISF is OK
        assert pack.is_fits_or_xisf is True
        # Check night log date format is OK
        assert re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', pack.night_log_date_string) is not None
        # Check detection of resource is OK
        assert pack.resource_type == 'observation'
        assert pack.remote_resources_name == 'observations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == 'HD5980'


@use_test_database
def test_packer_observation_with_filter():
    path = '/Users/onekiloparsec/data/HD5980/Halpha/dummy_010.fits'
    with patch('os.path.getsize', return_value=10), \
         patch.object(UploadPack, '_find_fits_filedate', return_value=datetime.now()), \
         patch.object(UploadPack, '_find_xisf_filedate', return_value=datetime.now()):
        pack = UploadPack(root_path, path, identity)
        assert pack is not None
        # Check detection of FITS or XISF is OK
        assert pack.is_fits_or_xisf is True
        # Check night log date format is OK
        assert re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', pack.night_log_date_string) is not None
        # Check detection of resource is OK
        assert pack.resource_type == 'observation'
        assert pack.remote_resources_name == 'observations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == 'HD5980/Halpha'


@use_test_database
def test_packer_observation_with_double_filter():
    path = '/Users/onekiloparsec/data/Tests/HD5980/Halpha/dummy_010.fits'
    with patch('os.path.getsize', return_value=10), \
         patch.object(UploadPack, '_find_fits_filedate', return_value=datetime.now()), \
         patch.object(UploadPack, '_find_xisf_filedate', return_value=datetime.now()):
        pack = UploadPack(root_path, path, identity)
        assert pack is not None
        # Check detection of FITS or XISF is OK
        assert pack.is_fits_or_xisf is True
        assert pack.has_date_obs is True
        # Check night log date format is OK
        assert re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', pack.night_log_date_string) is not None
        # Check detection of resource is OK
        assert pack.resource_type == 'observation'
        assert pack.remote_resources_name == 'observations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == 'Tests/HD5980/Halpha'


@use_test_database
def test_packer_calibration_no_date_obs():
    path = '/Users/onekiloparsec/data/Biases/dummy_010.fits'
    with patch('os.path.getsize', return_value=10), \
         patch.object(UploadPack, '_find_fits_filedate', return_value=None), \
         patch.object(UploadPack, '_find_xisf_filedate', return_value=None):
        pack = UploadPack(root_path, path, identity)
        assert pack is not None
        # Check detection of FITS or XISF is OK
        assert pack.is_fits_or_xisf is True
        assert pack.has_date_obs is False
        # Check night log date format is OK
        assert pack.night_log_date_string == ''
        # Check detection of resource is OK
        assert pack.resource_type == 'calibration'
        assert pack.remote_resources_name == 'calibrations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == 'Biases'


@use_test_database
def test_packer_calibration_no_fits_no_xisf():
    path = '/Users/onekiloparsec/data/Biases/dummy_010.csv'
    with patch('os.path.getsize', return_value=10), \
         patch.object(UploadPack, '_find_fits_filedate', return_value=None), \
         patch.object(UploadPack, '_find_xisf_filedate', return_value=None):
        pack = UploadPack(root_path, path, identity)
        assert pack is not None
        # Check detection of FITS or XISF is OK
        assert pack.is_fits_or_xisf is False
        assert pack.has_date_obs is False
        # Check night log date format is OK
        assert pack.night_log_date_string == ''
        # Check detection of resource is OK
        assert pack.resource_type == 'calibration'
        assert pack.remote_resources_name == 'calibrations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == 'Biases'


@use_test_database
def test_packer_no_telescope_date_after_noon():
    path = '/Users/onekiloparsec/data/Biases/dummy_010.fits'
    obs_date = datetime.fromisoformat('2020-03-21T20:56:35.450686')
    with patch('os.path.getsize', return_value=10), \
         patch.object(UploadPack, '_find_fits_filedate', return_value=obs_date), \
         patch.object(UploadPack, '_find_xisf_filedate', return_value=None):
        pack = UploadPack(root_path, path, identity)
        assert pack.night_log_date_string == '2020-03-21'


@use_test_database
def test_packer_no_telescope_date_before_noon():
    path = '/Users/onekiloparsec/data/Biases/dummy_010.fits'
    obs_date = datetime.fromisoformat('2020-03-21T07:56:35.450686')
    with patch('os.path.getsize', return_value=10), \
         patch.object(UploadPack, '_find_fits_filedate', return_value=obs_date), \
         patch.object(UploadPack, '_find_xisf_filedate', return_value=None):
        pack = UploadPack(root_path, path, identity)
        assert pack.night_log_date_string == '2020-03-20'
