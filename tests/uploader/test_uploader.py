import importlib
import os
import uuid
from unittest.mock import patch

from arcsecond.api.main import ArcsecondAPI

from oort.shared.identity import Identity
from oort.shared.models import Calibration, Dataset, NightLog, Observation, Organisation, Telescope, Upload, db
from oort.uploader.engine.packer import UploadPack
from oort.uploader.engine.uploader import FileUploader
from tests.utils import (TEST_CUSTOM_API_KEY, TEST_CUSTOM_USERNAME, TEST_LOGIN_API_KEY, TEST_LOGIN_ORG_ROLE,
                         TEST_LOGIN_ORG_SUBDOMAIN, TEST_LOGIN_USERNAME, use_test_database)

spec = importlib.util.find_spec('oort')

folder_path = os.path.join(os.path.dirname(spec.origin), '..', 'tests', 'fixtures')
fits_file_name = 'very_simple.fits'
fits_file_path = os.path.join(folder_path, fits_file_name)

telescope_uuid = '44f5bee9-a557-4264-86d6-c877d5013788'

db.connect(reuse_if_open=True)
db.create_tables([Organisation, Telescope, NightLog, Observation, Calibration, Dataset, Upload])


@use_test_database
def test_uploader_init_no_org():
    identity = Identity(TEST_LOGIN_USERNAME, TEST_LOGIN_API_KEY, debug=True)
    pack = UploadPack(folder_path, fits_file_path, identity)
    dataset = Dataset.smart_create(uuid=str(uuid.uuid4()))
    pack.upload.smart_update(dataset=dataset)

    with patch.object(ArcsecondAPI, 'datafiles') as mock_api:
        uploader = FileUploader(pack)

        mock_api.assert_called_with(debug=True, test=True, api_key=TEST_LOGIN_API_KEY, dataset=dataset.uuid)
        assert uploader is not None


@use_test_database
def test_uploader_init_org():
    identity = Identity(TEST_LOGIN_USERNAME,
                        '',
                        TEST_LOGIN_ORG_SUBDOMAIN,
                        TEST_LOGIN_ORG_ROLE,
                        telescope_uuid,
                        debug=True)

    pack = UploadPack(folder_path, fits_file_path, identity)
    dataset = Dataset.smart_create(uuid=str(uuid.uuid4()))
    pack.upload.smart_update(dataset=dataset)

    with patch.object(ArcsecondAPI, 'datafiles') as mock_api:
        uploader = FileUploader(pack)

        mock_api.assert_called_with(debug=True, test=True, organisation=TEST_LOGIN_ORG_SUBDOMAIN, dataset=dataset.uuid)
        assert uploader is not None


@use_test_database
def test_uploader_init_org_custom_astronomer():
    identity = Identity(TEST_CUSTOM_USERNAME,
                        TEST_CUSTOM_API_KEY,
                        TEST_LOGIN_ORG_SUBDOMAIN,
                        TEST_LOGIN_ORG_ROLE,
                        telescope_uuid,
                        debug=True)

    pack = UploadPack(folder_path, fits_file_path, identity)
    dataset = Dataset.smart_create(uuid=str(uuid.uuid4()))
    pack.upload.smart_update(dataset=dataset)

    with patch.object(ArcsecondAPI, 'datafiles') as mock_api:
        uploader = FileUploader(pack)

        mock_api.assert_called_with(debug=True, test=True, api_key=TEST_CUSTOM_API_KEY, dataset=dataset.uuid)
        assert uploader is not None
