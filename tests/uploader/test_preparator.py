import importlib
import pathlib
import socket
import uuid
from unittest.mock import patch

from arcsecond.api.main import ArcsecondAPI

from oort import __version__
from oort.shared.identity import Identity
from oort.shared.models import Dataset, Organisation, Telescope, Upload, db
from oort.uploader.engine.packer import UploadPack
from oort.uploader.engine.preparator import UploadPreparator
from tests.utils import (ORG_DETAILS, TEL_DETAILS, TEL_UUID, TEST_LOGIN_ORG_ROLE, TEST_LOGIN_ORG_SUBDOMAIN,
                         TEST_LOGIN_UPLOAD_KEY, TEST_LOGIN_USERNAME, clear_arcsecond_test_credentials,
                         save_arcsecond_test_credentials, use_test_database)

spec = importlib.util.find_spec('oort')

fits_file_name = 'very_simple.fits'
folder_path = pathlib.Path(spec.origin).parent / 'tests' / 'fixtures'
fits_file_path = folder_path / fits_file_name

TAGS = [
    'oort|folder|fixtures',
    f'oort|root|{str(folder_path)}',
    f'oort|origin|{socket.gethostname()}',
    f'oort|uploader|{ArcsecondAPI.username()}',
    f'oort|version|{__version__}'
]

db.connect(reuse_if_open=True)
db.create_tables([Organisation, Telescope, Dataset, Upload])


@use_test_database
def test_preparator_init_no_org():
    clear_arcsecond_test_credentials()

    identity = Identity(TEST_LOGIN_USERNAME, TEST_LOGIN_UPLOAD_KEY, debug=True)
    pack = UploadPack(str(folder_path), str(fits_file_path), identity)
    pack.collect_file_info()

    with patch.object(UploadPreparator, 'prepare') as mock_method:
        prep = UploadPreparator(pack, identity)
        assert prep is not None
        assert mock_method.not_called()
        assert Organisation.select().count() == 0


@use_test_database
def test_preparator_init_with_org():
    save_arcsecond_test_credentials()

    identity = Identity(TEST_LOGIN_USERNAME,
                        TEST_LOGIN_UPLOAD_KEY,
                        TEST_LOGIN_ORG_SUBDOMAIN,
                        TEST_LOGIN_ORG_ROLE,
                        TEL_UUID,
                        debug=True)

    pack = UploadPack(str(folder_path), str(fits_file_path), identity)
    pack.collect_file_info()

    with patch.object(ArcsecondAPI, 'is_logged_in', return_value=True), \
            patch.object(UploadPreparator, 'prepare') as mock_method_prepare, \
            patch.object(ArcsecondAPI, 'read', return_value=(ORG_DETAILS, None)):
        assert Organisation.select().count() == 0
        prep = UploadPreparator(pack, identity)

        assert prep is not None
        mock_method_prepare.assert_not_called()
        org = Organisation.select(Organisation.subdomain == TEST_LOGIN_ORG_SUBDOMAIN).get()
        assert org is not None


@use_test_database
def test_preparator_prepare_no_org_no_telescope():
    save_arcsecond_test_credentials()

    identity = Identity(TEST_LOGIN_USERNAME, TEST_LOGIN_UPLOAD_KEY, debug=True)
    pack = UploadPack(str(folder_path), str(fits_file_path), identity)
    pack.collect_file_info()
    assert identity.telescope is None

    ds = {'uuid': str(uuid.uuid4()), 'name': pack.dataset_name}

    with patch.object(ArcsecondAPI, 'is_logged_in', return_value=True), \
            patch.object(ArcsecondAPI, 'list', return_value=([], None)) as mock_method_list, \
            patch.object(ArcsecondAPI, 'datasets', return_value=ArcsecondAPI(test=True)) as mock_method_datasets, \
            patch.object(ArcsecondAPI, 'create', return_value=(ds, None)) as mock_method_create:
        up = UploadPreparator(pack, identity)
        result = up.prepare()

        assert result is True
        mock_method_datasets.assert_called_with(test=True, debug=True, upload_key=TEST_LOGIN_UPLOAD_KEY)
        # The pure comma-delimited string is KEY for not duplicating the datasets
        mock_method_list.assert_called_with(tags=f"oort|folder|fixtures,oort|root|{folder_path}")
        mock_method_create.assert_called_with({'name': 'fixtures', 'tags': TAGS})


@use_test_database
def test_preparator_prepare_with_org_and_telescope():
    save_arcsecond_test_credentials()

    identity = Identity(TEST_LOGIN_USERNAME,
                        TEST_LOGIN_UPLOAD_KEY,
                        TEST_LOGIN_ORG_SUBDOMAIN,
                        TEST_LOGIN_ORG_ROLE,
                        TEL_UUID,
                        debug=True)

    pack = UploadPack(str(folder_path), str(fits_file_path), identity)
    pack.collect_file_info()
    assert identity.telescope is not None

    ds = {'uuid': str(uuid.uuid4()), 'name': pack.dataset_name}

    with patch.object(ArcsecondAPI, 'is_logged_in', return_value=True), \
            patch.object(ArcsecondAPI, 'read') as mock_method_read, \
            patch.object(ArcsecondAPI, 'list', return_value=([], None)), \
            patch.object(ArcsecondAPI, 'datasets', return_value=ArcsecondAPI(test=True)) as mock_method_datasets, \
            patch.object(ArcsecondAPI, 'create', return_value=(ds, None)) as mock_method_create:
        mock_method_read.side_effect = [(TEL_DETAILS, None), (ORG_DETAILS, None)]

        up = UploadPreparator(pack, identity)
        result = up.prepare()

        assert result is True
        mock_method_read.assert_called()
        mock_method_datasets.assert_called_with(test=True,
                                                debug=True,
                                                upload_key=TEST_LOGIN_UPLOAD_KEY,
                                                organisation=TEST_LOGIN_ORG_SUBDOMAIN)
        mock_method_create.assert_called_with({'name': 'fixtures', 'tags': TAGS + [f'oort|telescope|{TEL_UUID}']})
