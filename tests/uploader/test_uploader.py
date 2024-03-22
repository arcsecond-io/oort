import importlib
import os
from unittest.mock import patch

from arcsecond.api.main import ArcsecondAPI

from oort.common.identity import Identity
from oort.uploader.uploader import FileUploader
from tests.utils import (TEST_CUSTOM_UPLOAD_KEY, TEST_CUSTOM_USERNAME, TEST_LOGIN_ORG_ROLE, TEST_LOGIN_ORG_SUBDOMAIN,
                         TEST_LOGIN_UPLOAD_KEY, TEST_LOGIN_USERNAME)

spec = importlib.util.find_spec('oort')

folder_path = os.path.join(os.path.dirname(spec.origin), '..', 'tests', 'fixtures')
fits_file_name = 'very_simple.fits'
fits_file_path = os.path.join(folder_path, fits_file_name)

telescope_uuid = '44f5bee9-a557-4264-86d6-c877d5013788'


def test_uploader_init_no_org():
    identity = Identity(TEST_LOGIN_USERNAME, TEST_LOGIN_UPLOAD_KEY, api='test')
    pack = UploadPack(folder_path, fits_file_path, identity)
    pack.collect_file_info()

    with patch.object(ArcsecondAPI, 'datafiles') as mock_api:
        uploader = FileUploader(pack)

        mock_api.assert_called_with(test=True,
                                    upload_key=TEST_LOGIN_UPLOAD_KEY,
                                    dataset=dataset.uuid,
                                    organisation='',
                                    api='test')
        assert uploader is not None


def test_uploader_init_org():
    identity = Identity(TEST_LOGIN_USERNAME,
                        '',
                        TEST_LOGIN_ORG_SUBDOMAIN,
                        TEST_LOGIN_ORG_ROLE,
                        telescope_uuid,
                        api='test')

    pack = UploadPack(folder_path, fits_file_path, identity)
    pack.collect_file_info()

    pack.upload.smart_update(dataset=dataset)

    with patch.object(ArcsecondAPI, 'datafiles') as mock_api:
        uploader = FileUploader(pack)

        mock_api.assert_called_with(test=True,
                                    upload_key='',
                                    organisation=TEST_LOGIN_ORG_SUBDOMAIN,
                                    dataset=dataset.uuid,
                                    api='test')
        assert uploader is not None


def test_uploader_init_org_custom_astronomer():
    identity = Identity(TEST_CUSTOM_USERNAME,
                        TEST_CUSTOM_UPLOAD_KEY,
                        TEST_LOGIN_ORG_SUBDOMAIN,
                        TEST_LOGIN_ORG_ROLE,
                        telescope_uuid,
                        api='test')

    pack = UploadPack(folder_path, fits_file_path, identity)
    pack.collect_file_info()

    pack.upload.smart_update(dataset=dataset)

    with patch.object(ArcsecondAPI, 'datafiles') as mock_api:
        uploader = FileUploader(pack)

        mock_api.assert_called_with(test=True,
                                    upload_key=TEST_CUSTOM_UPLOAD_KEY,
                                    organisation=TEST_LOGIN_ORG_SUBDOMAIN,
                                    dataset=dataset.uuid,
                                    api='test')
        assert uploader is not None
