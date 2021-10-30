import importlib
import pathlib
import random
import re
import uuid
from datetime import datetime
from unittest.mock import patch

from oort.shared.identity import Identity
from oort.shared.utils import get_random_string
from oort.uploader.engine.packer import UploadPack
from tests.utils import use_test_database

spec = importlib.util.find_spec('oort')

root_path = pathlib.Path(spec.origin).parent.parent
fixture_path = root_path / 'tests' / 'fixtures'

telescope_uuid = '44f5bee9-a557-4264-86d6-c877d5013788'
identity = Identity('cedric', str(uuid.uuid4()), 'saao', 'admin', telescope_uuid, True)


@use_test_database
def test_packer_calib_bias():
    path = str(root_path / f'Biases{get_random_string(5)}' / 'dummy_001.fits')
    with patch('pathlib.Path.stat') as stat, \
            patch.object(UploadPack, '_find_fits_file_date_and_target_name', return_value=(datetime.now(), "target")), \
            patch.object(UploadPack, '_find_xisf_file_date_and_target_name', return_value=(datetime.now(), "target")):
        stat.return_value.st_size = random.randint(1, 1000)

        pack = UploadPack(str(root_path), path, identity)
        assert pack is not None

        pack.collect_file_info()
        assert pack.upload is not None
        # Check detection of FITS or XISF is OK
        assert pack.is_data_file is True
        assert pack.upload.file_path == path
        assert pack.upload.file_path_zipped == path + '.gz'
        assert pack.upload.file_size > 0
        assert pack.upload.file_size_zipped > 0
        assert pack.upload.astronomer == 'cedric'
        assert pack.upload.target_name == 'target'

        # Check night log date format is OK
        assert re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', pack.night_log_date_string) is not None
        # Check detection of resource is OK
        assert pack.resource_type == 'calibration'
        assert pack.remote_resources_name == 'calibrations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == '/'.join(path.split('/')[-3:-1])


@use_test_database
def test_packer_calib_dark():
    path = str(root_path / f'dArkss{get_random_string(5)}' / 'dummy_001.fits')
    with patch('pathlib.Path.stat') as stat, \
            patch.object(UploadPack, '_find_fits_file_date_and_target_name', return_value=(datetime.now(), "target")), \
            patch.object(UploadPack, '_find_xisf_file_date_and_target_name', return_value=(datetime.now(), "target")):
        stat.return_value.st_size = random.randint(1, 1000)

        pack = UploadPack(str(root_path), path, identity)
        assert pack is not None

        pack.collect_file_info()
        # Check detection of FITS or XISF is OK
        assert pack.is_data_file is True
        assert pack.upload.file_path == path
        assert pack.upload.file_path_zipped == path + '.gz'
        assert pack.upload.file_size > 0
        assert pack.upload.file_size_zipped > 0
        assert pack.upload.target_name == 'target'

        # Check night log date format is OK
        assert re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', pack.night_log_date_string) is not None
        # Check detection of resource is OK
        assert pack.resource_type == 'calibration'
        assert pack.remote_resources_name == 'calibrations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == '/'.join(path.split('/')[-3:-1])


@use_test_database
def test_packer_calibs_flat_no_filter():
    path = str(root_path / f'FLATS{get_random_string(5)}' / 'dummy_001.fits')
    with patch('pathlib.Path.stat') as stat, \
            patch.object(UploadPack, '_find_fits_file_date_and_target_name', return_value=(datetime.now(), "target")), \
            patch.object(UploadPack, '_find_xisf_file_date_and_target_name', return_value=(datetime.now(), "target")):
        stat.return_value.st_size = random.randint(1, 1000)

        pack = UploadPack(str(root_path), path, identity)
        assert pack is not None

        pack.collect_file_info()
        # Check detection of FITS or XISF is OK
        assert pack.is_data_file is True
        assert pack.upload.file_path == path
        assert pack.upload.file_path_zipped == path + '.gz'
        assert pack.upload.file_size > 0
        assert pack.upload.file_size_zipped > 0
        assert pack.upload.target_name == 'target'

        # Check night log date format is OK
        assert re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', pack.night_log_date_string) is not None
        # Check detection of resource is OK
        assert pack.resource_type == 'calibration'
        assert pack.remote_resources_name == 'calibrations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == '/'.join(path.split('/')[-3:-1])


@use_test_database
def test_packer_calibs_flat_with_filter():
    path = str(root_path / f'FLATS{get_random_string(5)}' / 'U' / 'dummy_001.fits')
    with patch('pathlib.Path.stat') as stat, \
            patch.object(UploadPack, '_find_fits_file_date_and_target_name', return_value=(datetime.now(), "target")), \
            patch.object(UploadPack, '_find_xisf_file_date_and_target_name', return_value=(datetime.now(), "target")):
        stat.return_value.st_size = random.randint(1, 1000)

        pack = UploadPack(str(root_path), path, identity)
        assert pack is not None

        pack.collect_file_info()
        # Check detection of FITS or XISF is OK
        assert pack.is_data_file is True
        assert pack.upload.file_path == path
        assert pack.upload.file_path_zipped == path + '.gz'
        assert pack.upload.file_size > 0
        assert pack.upload.file_size_zipped > 0
        assert pack.upload.target_name == 'target'

        # Check night log date format is OK
        assert re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', pack.night_log_date_string) is not None
        # Check detection of resource is OK
        assert pack.resource_type == 'calibration'
        assert pack.remote_resources_name == 'calibrations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == '/'.join(path.split('/')[-4:-1])


@use_test_database
def test_packer_observation_no_filter():
    path = str(root_path / 'HD5980' / 'dummy_010.fits')
    with patch('pathlib.Path.stat') as stat, \
            patch.object(UploadPack, '_find_fits_file_date_and_target_name', return_value=(datetime.now(), "target")), \
            patch.object(UploadPack, '_find_xisf_file_date_and_target_name', return_value=(datetime.now(), "target")):
        stat.return_value.st_size = random.randint(1, 1000)

        pack = UploadPack(str(root_path), path, identity)
        assert pack is not None

        pack.collect_file_info()
        # Check detection of FITS or XISF is OK
        assert pack.is_data_file is True
        assert pack.upload.file_path == path
        assert pack.upload.file_path_zipped == path + '.gz'
        assert pack.upload.file_size > 0
        assert pack.upload.file_size_zipped > 0
        assert pack.upload.target_name == 'target'

        # Check night log date format is OK
        assert re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', pack.night_log_date_string) is not None
        # Check detection of resource is OK
        # assert pack.resource_type == 'observation'
        # assert pack.remote_resources_name == 'observations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == '/'.join(path.split('/')[-3:-1])


@use_test_database
def test_packer_observation_with_filter():
    path = str(root_path / 'HD5980' / 'Halpha' / 'dummy_010.fits')
    with patch('pathlib.Path.stat') as stat, \
            patch.object(UploadPack, '_find_fits_file_date_and_target_name', return_value=(datetime.now(), "target")), \
            patch.object(UploadPack, '_find_xisf_file_date_and_target_name', return_value=(datetime.now(), "target")):
        stat.return_value.st_size = random.randint(1, 1000)

        pack = UploadPack(str(root_path), path, identity)
        assert pack is not None

        pack.collect_file_info()
        # Check detection of FITS or XISF is OK
        assert pack.is_data_file is True
        assert pack.upload.file_path == path
        assert pack.upload.file_path_zipped == path + '.gz'
        assert pack.upload.file_size > 0
        assert pack.upload.file_size_zipped > 0
        assert pack.upload.target_name == 'target'

        # Check night log date format is OK
        assert re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', pack.night_log_date_string) is not None
        # Check detection of resource is OK
        # assert pack.resource_type == 'observation'
        # assert pack.remote_resources_name == 'observations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == '/'.join(path.split('/')[-4:-1])


@use_test_database
def test_packer_observation_with_double_filter():
    path = str(root_path / 'Tests' / 'HD5980' / 'Halpha' / 'dummy_010.fits')
    with patch('pathlib.Path.stat') as stat, \
            patch.object(UploadPack, '_find_fits_file_date_and_target_name', return_value=(datetime.now(), "target")), \
            patch.object(UploadPack, '_find_xisf_file_date_and_target_name', return_value=(datetime.now(), "target")):
        stat.return_value.st_size = random.randint(1, 1000)

        pack = UploadPack(str(root_path), path, identity)
        assert pack is not None

        pack.collect_file_info()
        # Check detection of FITS or XISF is OK
        assert pack.is_data_file is True
        assert pack.upload.file_path == path
        assert pack.upload.file_path_zipped == path + '.gz'
        assert pack.upload.file_size > 0
        assert pack.upload.file_size_zipped > 0

        assert pack.has_date_obs is True
        # Check night log date format is OK
        assert re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', pack.night_log_date_string) is not None
        # Check detection of resource is OK
        # assert pack.resource_type == 'observation'
        # assert pack.remote_resources_name == 'observations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == '/'.join(path.split('/')[-5:-1])


@use_test_database
def test_packer_calibration_no_date_obs():
    path = str(root_path / 'Biases' / 'dummy_010.fits')
    with patch('pathlib.Path.stat') as stat, \
            patch.object(UploadPack, '_find_fits_file_date_and_target_name', return_value=(None, "")), \
            patch.object(UploadPack, '_find_xisf_file_date_and_target_name', return_value=(None, "")):
        stat.return_value.st_size = random.randint(1, 1000)

        pack = UploadPack(str(root_path), path, identity)
        assert pack is not None

        pack.collect_file_info()
        # Check detection of FITS or XISF is OK
        assert pack.is_data_file is True
        assert pack.upload.file_path == path
        assert pack.upload.file_path_zipped == path + '.gz'
        assert pack.upload.file_size > 0
        assert pack.upload.file_size_zipped > 0

        assert pack.has_date_obs is False
        # Check night log date format is OK
        assert pack.night_log_date_string == ''
        # Check detection of resource is OK
        # assert pack.resource_type == 'calibration'
        # assert pack.remote_resources_name == 'calibrations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == '/'.join(path.split('/')[-3:-1])


@use_test_database
def test_packer_calibration_no_fits_no_xisf():
    path = str(root_path / 'Biases' / 'dummy_010.csv')
    with patch('pathlib.Path.stat') as stat, \
            patch.object(UploadPack, '_find_fits_file_date_and_target_name', return_value=(None, "")), \
            patch.object(UploadPack, '_find_xisf_file_date_and_target_name', return_value=(None, "")):
        stat.return_value.st_size = random.randint(1, 1000)

        pack = UploadPack(str(root_path), path, identity)
        assert pack is not None

        pack.collect_file_info()
        # Check detection of FITS or XISF is OK
        assert pack.is_data_file is False
        assert pack.upload.file_path == path
        assert pack.upload.file_path_zipped == path + '.gz'
        assert pack.upload.file_size > 0
        assert pack.upload.file_size_zipped > 0

        assert pack.has_date_obs is False
        # Check night log date format is OK
        assert pack.night_log_date_string == ''
        # Check detection of resource is OK
        # assert pack.resource_type == 'calibration'
        # assert pack.remote_resources_name == 'calibrations'
        # Check name of dataset respect folder name
        assert pack.dataset_name == '/'.join(path.split('/')[-3:-1])


@use_test_database
def test_packer_no_telescope_date_after_noon():
    path = str(root_path / 'Biases' / 'dummy_010.fits')
    obs_date = datetime(2020, 3, 21, hour=20, minute=56, second=35)
    with patch('os.path.getsize', return_value=10), \
            patch.object(UploadPack, '_find_fits_file_date_and_target_name', return_value=(obs_date, "target")), \
            patch.object(UploadPack, '_find_xisf_file_date_and_target_name', return_value=(None, "")):
        pack = UploadPack(str(root_path), path, identity)
        pack.collect_file_info()
        assert pack.night_log_date_string == '2020-03-21'


@use_test_database
def test_packer_no_telescope_date_before_noon():
    path = str(root_path / 'Biases' / 'dummy_010.fits')
    obs_date = datetime(2020, 3, 21, hour=7, minute=56, second=35)
    with patch('os.path.getsize', return_value=10), \
            patch.object(UploadPack, '_find_fits_file_date_and_target_name', return_value=(obs_date, "target")), \
            patch.object(UploadPack, '_find_xisf_file_date_and_target_name', return_value=(None, "")):
        pack = UploadPack(str(root_path), path, identity)
        pack.collect_file_info()
        assert pack.night_log_date_string == '2020-03-20'


# ############# REAL FIXTURE FILES ################################################################################### #

@use_test_database
def test_packer_non_data_non_zipped():
    path = str(fixture_path / 'non_data_non_zipped.txt')
    pack = UploadPack(str(root_path), path, identity)
    pack.collect_file_info()
    assert pack.is_data_file is False
    assert pack.is_hidden_file is False
    assert pack.clear_file_exists is True
    assert pack.zipped_file_exists is False
    assert pack.should_zip is False


@use_test_database
def test_packer_non_data_non_zipped_added_gz():
    path = str(fixture_path / 'non_data_non_zipped.txt.gz')
    pack = UploadPack(str(root_path), path, identity)
    pack.collect_file_info()
    assert pack.is_data_file is False
    assert pack.is_hidden_file is False
    assert pack.clear_file_exists is True
    assert pack.zipped_file_exists is False
    assert pack.should_zip is False


@use_test_database
def test_packer_non_data_zipped():
    path = str(fixture_path / 'non_data_zipped.txt.gz')
    pack = UploadPack(str(root_path), path, identity)
    pack.collect_file_info()
    assert pack.is_data_file is False
    assert pack.is_hidden_file is False
    assert pack.clear_file_exists is False
    assert pack.zipped_file_exists is True
    assert pack.should_zip is False


@use_test_database
def test_packer_data_clear_with_zipped():
    path = str(fixture_path / 'data_zipped_with_clear.fits')
    pack = UploadPack(str(root_path), path, identity)
    pack.collect_file_info()
    assert pack.is_data_file is True
    assert pack.is_hidden_file is False
    assert pack.clear_file_exists is True
    assert pack.zipped_file_exists is True
    assert pack.should_zip is True


@use_test_database
def test_packer_data_clear_with_zipped_added_gz():
    path = str(fixture_path / 'data_zipped_with_clear.fits.gz')
    pack = UploadPack(str(root_path), path, identity)
    pack.collect_file_info()
    assert pack.is_data_file is True
    assert pack.is_hidden_file is False
    assert pack.clear_file_exists is True
    assert pack.zipped_file_exists is True
    assert pack.should_zip is True


@use_test_database
def test_packer_data_zip_with_clear():
    path = str(fixture_path / 'data_zipped_with_clear.fits.zip')
    pack = UploadPack(str(root_path), path, identity)
    pack.collect_file_info()
    assert pack.is_data_file is True
    assert pack.is_hidden_file is False
    assert pack.clear_file_exists is True
    assert pack.zipped_file_exists is True
    assert pack.should_zip is True


@use_test_database
def test_packer_data_gzip_with_clear():
    path = str(fixture_path / 'data_zipped_with_clear.fits.gz')
    pack = UploadPack(str(root_path), path, identity)
    pack.collect_file_info()
    assert pack.is_data_file is True
    assert pack.is_hidden_file is False
    assert pack.clear_file_exists is True
    assert pack.zipped_file_exists is True
    assert pack.should_zip is True


@use_test_database
def test_packer_data_bz2_with_clear():
    path = str(fixture_path / 'data_zipped_with_clear.fits.bz2')
    pack = UploadPack(str(root_path), path, identity)
    pack.collect_file_info()
    assert pack.is_data_file is True
    assert pack.is_hidden_file is False
    assert pack.clear_file_exists is True
    assert pack.zipped_file_exists is True
    assert pack.should_zip is True


@use_test_database
def test_packer_data_clear_no_clear():
    path = str(fixture_path / 'data_zipped_no_clear.fits')
    pack = UploadPack(str(root_path), path, identity)
    pack.collect_file_info()
    assert pack.is_data_file is True
    assert pack.is_hidden_file is False
    assert pack.clear_file_exists is False
    assert pack.zipped_file_exists is True
    assert pack.should_zip is False


@use_test_database
def test_packer_data_zip_no_clear():
    path = str(fixture_path / 'data_zipped_no_clear.fits.zip')
    pack = UploadPack(str(root_path), path, identity)
    pack.collect_file_info()
    assert pack.is_data_file is True
    assert pack.is_hidden_file is False
    assert pack.clear_file_exists is False
    assert pack.zipped_file_exists is True
    assert pack.should_zip is False


@use_test_database
def test_packer_data_gzip_no_clear():
    path = str(fixture_path / 'data_zipped_no_clear.fits.gz')
    pack = UploadPack(str(root_path), path, identity)
    pack.collect_file_info()
    assert pack.is_data_file is True
    assert pack.is_hidden_file is False
    assert pack.clear_file_exists is False
    assert pack.zipped_file_exists is True
    assert pack.should_zip is False


@use_test_database
def test_packer_data_bz2_no_clear():
    path = str(fixture_path / 'data_zipped_no_clear.fits.bz2')
    pack = UploadPack(str(root_path), path, identity)
    pack.collect_file_info()
    assert pack.is_data_file is True
    assert pack.is_hidden_file is False
    assert pack.clear_file_exists is False
    assert pack.zipped_file_exists is True
    assert pack.should_zip is False


@use_test_database
def test_packer_data_pure_zip():
    path = str(fixture_path / 'dummy.zip')
    pack = UploadPack(str(root_path), path, identity)
    pack.collect_file_info()
    assert pack.clear_file_path.endswith('dummy.zip')


@use_test_database
def test_packer_data_txt_zip():
    path = str(fixture_path / 'dummy.txt.zip')
    pack = UploadPack(str(root_path), path, identity)
    pack.collect_file_info()
    assert pack.clear_file_path.endswith('dummy.txt')
