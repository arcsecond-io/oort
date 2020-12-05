import importlib
import os
import uuid
from unittest.mock import patch

from arcsecond.api.main import ArcsecondAPI

from oort.shared.identity import Identity
from oort.shared.models import Calibration, Dataset, NightLog, Observation, Organisation, Telescope, Upload, db
from oort.uploader.engine.packer import UploadPack
from oort.uploader.engine.preparator import UploadPreparator
from tests.utils import (TEST_LOGIN_API_KEY, TEST_CUSTOM_API_KEY, TEST_CUSTOM_USERNAME, TEST_LOGIN_ORG_ROLE,
                         TEST_LOGIN_ORG_SUBDOMAIN, TEST_LOGIN_USERNAME, save_test_credentials, use_test_database)

spec = importlib.util.find_spec('oort')

folder_path = os.path.join(os.path.dirname(spec.origin), '..', 'tests', 'fixtures')
fits_file_name = 'very_simple.fits'
fits_file_path = os.path.join(folder_path, fits_file_name)

telescope_uuid = '44f5bee9-a557-4264-86d6-c877d5013788'

db.connect(reuse_if_open=True)
db.create_tables([Organisation, Telescope, NightLog, Observation, Calibration, Dataset, Upload])


@use_test_database
def test_preparator_init_no_org():
    identity = Identity('cedric', str(uuid.uuid4()), debug=True)
    pack = UploadPack(folder_path, fits_file_path, identity)
    with patch.object(UploadPreparator, 'prepare') as mock_method:
        prep = UploadPreparator(pack, Identity('cedric', str(uuid.uuid4()), debug=True))
        assert prep is not None
        assert prep.preparation_succeeded is False
        assert prep.telescope is None
        assert prep.night_log is None
        assert prep.obs_or_calib is None
        assert prep.dataset is None
        assert mock_method.not_called()
        assert Organisation.select().count() == 0


@use_test_database
def test_preparator_init_with_org():
    save_test_credentials()

    identity = Identity(TEST_LOGIN_USERNAME,
                        '',
                        TEST_LOGIN_ORG_SUBDOMAIN,
                        TEST_LOGIN_ORG_ROLE,
                        telescope_uuid,
                        debug=True)

    org_details = {'subdomain': TEST_LOGIN_ORG_SUBDOMAIN}

    pack = UploadPack(folder_path, fits_file_path, identity)
    with patch.object(ArcsecondAPI, 'is_logged_in', return_value=True), \
         patch.object(UploadPreparator, 'prepare') as mock_method_prepare, \
            patch.object(ArcsecondAPI, 'read', return_value=(org_details, None)) as mock_method_read:
        assert Organisation.select().count() == 0
        prep = UploadPreparator(pack, identity)

        assert prep is not None
        assert prep.preparation_succeeded is False
        assert prep.telescope is None
        assert prep.night_log is None
        assert prep.obs_or_calib is None
        assert prep.dataset is None

        mock_method_prepare.assert_not_called()
        mock_method_read.assert_called_with(TEST_LOGIN_ORG_SUBDOMAIN)
        # mock_method_read.assert_called_with(date=pack.night_log_date_string)
        org = Organisation.select(Organisation.subdomain == TEST_LOGIN_ORG_SUBDOMAIN).get()
        assert org is not None


@use_test_database
def test_preparator_init_with_org_and_custom_astronomer():
    save_test_credentials()

    identity = Identity(TEST_CUSTOM_USERNAME,
                        TEST_CUSTOM_API_KEY,
                        TEST_LOGIN_ORG_SUBDOMAIN,
                        TEST_LOGIN_ORG_ROLE,
                        telescope_uuid,
                        debug=True)

    org_details = {'subdomain': TEST_LOGIN_ORG_SUBDOMAIN}

    pack = UploadPack(folder_path, fits_file_path, identity)
    with patch.object(ArcsecondAPI, 'is_logged_in', return_value=True), \
         patch.object(UploadPreparator, 'prepare') as mock_method_prepare, \
            patch.object(ArcsecondAPI, 'read', return_value=(org_details, None)) as mock_method_read:
        assert Organisation.select().count() == 0
        prep = UploadPreparator(pack, identity)

        assert prep is not None
        assert prep.preparation_succeeded is False
        assert prep.telescope is None
        assert prep.night_log is None
        assert prep.obs_or_calib is None
        assert prep.dataset is None

        mock_method_prepare.assert_not_called()
        mock_method_read.assert_called_with(TEST_LOGIN_ORG_SUBDOMAIN)
        # mock_method_read.assert_called_with(date=pack.night_log_date_string)
        org = Organisation.select(Organisation.subdomain == TEST_LOGIN_ORG_SUBDOMAIN).get()
        assert org is not None


@use_test_database
def test_preparator_prepare_no_org_no_telescope():
    save_test_credentials()

    identity = Identity(TEST_LOGIN_USERNAME, TEST_LOGIN_API_KEY, debug=True)
    pack = UploadPack(folder_path, fits_file_path, identity)
    assert len(pack.night_log_date_string) > 0
    assert identity.telescope is None

    nl = {'uuid': str(uuid.uuid4()), 'date': pack.night_log_date_string}
    obs = {'uuid': str(uuid.uuid4()), 'night_log': nl['uuid'], 'name': pack.dataset_name}
    ds = {'uuid': str(uuid.uuid4()), 'observation': obs['uuid'], 'name': pack.dataset_name}

    with patch.object(ArcsecondAPI, 'is_logged_in', return_value=True), \
         patch.object(ArcsecondAPI, 'list', return_value=([], None)) as mock_method_list, \
            patch.object(ArcsecondAPI, 'nightlogs', return_value=ArcsecondAPI(test=True)) as mock_method_nightlogs, \
            patch.object(ArcsecondAPI, 'observations', return_value=ArcsecondAPI(test=True)) as mock_method_obs, \
            patch.object(ArcsecondAPI, 'datasets', return_value=ArcsecondAPI(test=True)) as mock_method_datasets, \
            patch.object(ArcsecondAPI, 'create') as mock_method_create:
        mock_method_create.side_effect = [(nl, None), (obs, None), (ds, None)]

        up = UploadPreparator(pack, identity)
        up.prepare()

        mock_method_nightlogs.assert_called_with(test=True, debug=True, api_key=TEST_LOGIN_API_KEY)
        mock_method_obs.assert_called_with(test=True, debug=True, api_key=TEST_LOGIN_API_KEY)
        mock_method_datasets.assert_called_with(test=True, debug=True, api_key=TEST_LOGIN_API_KEY)

        mock_method_list.assert_any_call(date=pack.night_log_date_string)
        mock_method_list.assert_any_call(name=pack.dataset_name, night_log=nl['uuid'], target_name=pack.dataset_name)
        mock_method_list.assert_any_call(name=pack.dataset_name, observation=obs['uuid'])

        mock_method_create.assert_any_call({'date': pack.night_log_date_string})
        assert up.night_log is not None
        assert up.night_log.uuid == nl['uuid']

        payload = {'name': pack.dataset_name, 'night_log': nl['uuid'], 'target_name': pack.dataset_name}
        mock_method_create.assert_any_call(payload)
        assert up.obs_or_calib is not None
        assert up.obs_or_calib.uuid == obs['uuid']

        mock_method_create.assert_any_call({'name': pack.dataset_name, 'observation': obs['uuid']})
        assert up.dataset is not None
        assert up.dataset.uuid == ds['uuid']


@use_test_database
def test_preparator_prepare_with_org_and_telescope():
    save_test_credentials()

    identity = Identity(TEST_LOGIN_USERNAME,
                        '',
                        TEST_LOGIN_ORG_SUBDOMAIN,
                        TEST_LOGIN_ORG_ROLE,
                        telescope_uuid,
                        debug=True)

    org_details = {'subdomain': TEST_LOGIN_ORG_SUBDOMAIN}

    pack = UploadPack(folder_path, fits_file_path, identity)
    assert len(pack.night_log_date_string) > 0
    assert identity.telescope is not None

    nl = {'uuid': str(uuid.uuid4()), 'date': pack.night_log_date_string}
    obs = {'uuid': str(uuid.uuid4()), 'night_log': nl['uuid'], 'name': pack.dataset_name}
    ds = {'uuid': str(uuid.uuid4()), 'observation': obs['uuid'], 'name': pack.dataset_name}

    with patch.object(ArcsecondAPI, 'is_logged_in', return_value=True), \
         patch.object(ArcsecondAPI, 'list', return_value=([], None)) as mock_method_list, \
            patch.object(ArcsecondAPI, 'nightlogs', return_value=ArcsecondAPI(test=True)) as mock_method_nightlogs, \
            patch.object(ArcsecondAPI, 'observations', return_value=ArcsecondAPI(test=True)) as mock_method_obs, \
            patch.object(ArcsecondAPI, 'datasets', return_value=ArcsecondAPI(test=True)) as mock_method_datasets, \
            patch.object(ArcsecondAPI, 'read', return_value=(org_details, None)) as mock_method_read, \
            patch.object(ArcsecondAPI, 'create') as mock_method_create:
        mock_method_create.side_effect = [(nl, None), (obs, None), (ds, None)]

        up = UploadPreparator(pack, identity)
        up.prepare()

        mock_method_nightlogs.assert_called_with(test=True, debug=True, organisation=TEST_LOGIN_ORG_SUBDOMAIN)
        mock_method_obs.assert_called_with(test=True, debug=True, organisation=TEST_LOGIN_ORG_SUBDOMAIN)
        mock_method_datasets.assert_called_with(test=True, debug=True, organisation=TEST_LOGIN_ORG_SUBDOMAIN)

        mock_method_list.assert_any_call(date=pack.night_log_date_string, telescope=telescope_uuid)
        mock_method_list.assert_any_call(name=pack.dataset_name, night_log=nl['uuid'], target_name=pack.dataset_name)
        mock_method_list.assert_any_call(name=pack.dataset_name, observation=obs['uuid'])

        mock_method_create.assert_any_call({'date': pack.night_log_date_string, 'telescope': telescope_uuid})
        assert up.night_log is not None
        assert up.night_log.uuid == nl['uuid']

        payload = {'name': pack.dataset_name, 'night_log': nl['uuid'], 'target_name': pack.dataset_name}
        mock_method_create.assert_any_call(payload)
        assert up.obs_or_calib is not None
        assert up.obs_or_calib.uuid == obs['uuid']

        mock_method_create.assert_any_call({'name': pack.dataset_name, 'observation': obs['uuid']})
        assert up.dataset is not None
        assert up.dataset.uuid == ds['uuid']


@use_test_database
def test_preparator_prepare_with_org_and_telescope_and_custom_astronomer():
    save_test_credentials()

    identity = Identity(TEST_CUSTOM_USERNAME,
                        TEST_CUSTOM_API_KEY,
                        TEST_LOGIN_ORG_SUBDOMAIN,
                        TEST_LOGIN_ORG_ROLE,
                        telescope_uuid,
                        debug=True)

    org_details = {'subdomain': TEST_LOGIN_ORG_SUBDOMAIN}

    pack = UploadPack(folder_path, fits_file_path, identity)
    assert len(pack.night_log_date_string) > 0
    assert identity.telescope is not None

    nl = {'uuid': str(uuid.uuid4()), 'date': pack.night_log_date_string}
    obs = {'uuid': str(uuid.uuid4()), 'night_log': nl['uuid'], 'name': pack.dataset_name}
    ds = {'uuid': str(uuid.uuid4()), 'observation': obs['uuid'], 'name': pack.dataset_name}

    with patch.object(ArcsecondAPI, 'is_logged_in', return_value=True), \
         patch.object(ArcsecondAPI, 'list', return_value=([], None)) as mock_method_list, \
            patch.object(ArcsecondAPI, 'nightlogs', return_value=ArcsecondAPI(test=True)) as mock_method_nightlogs, \
            patch.object(ArcsecondAPI, 'observations', return_value=ArcsecondAPI(test=True)) as mock_method_obs, \
            patch.object(ArcsecondAPI, 'datasets', return_value=ArcsecondAPI(test=True)) as mock_method_datasets, \
            patch.object(ArcsecondAPI, 'read', return_value=(org_details, None)) as mock_method_read, \
            patch.object(ArcsecondAPI, 'create') as mock_method_create:
        mock_method_create.side_effect = [(nl, None), (obs, None), (ds, None)]

        up = UploadPreparator(pack, identity)
        up.prepare()

        # Making sure we build APIs with custom api_key and not organisation
        mock_method_nightlogs.assert_called_with(test=True, debug=True, api_key=TEST_CUSTOM_API_KEY)
        mock_method_obs.assert_called_with(test=True, debug=True, api_key=TEST_CUSTOM_API_KEY)
        mock_method_datasets.assert_called_with(test=True, debug=True, api_key=TEST_CUSTOM_API_KEY)

        mock_method_list.assert_any_call(date=pack.night_log_date_string, telescope=telescope_uuid)
        mock_method_list.assert_any_call(name=pack.dataset_name, night_log=nl['uuid'], target_name=pack.dataset_name)
        mock_method_list.assert_any_call(name=pack.dataset_name, observation=obs['uuid'])

        mock_method_create.assert_any_call({'date': pack.night_log_date_string, 'telescope': telescope_uuid})
        assert up.night_log is not None
        assert up.night_log.uuid == nl['uuid']

        payload = {'name': pack.dataset_name, 'night_log': nl['uuid'], 'target_name': pack.dataset_name}
        mock_method_create.assert_any_call(payload)
        assert up.obs_or_calib is not None
        assert up.obs_or_calib.uuid == obs['uuid']

        mock_method_create.assert_any_call({'name': pack.dataset_name, 'observation': obs['uuid']})
        assert up.dataset is not None
        assert up.dataset.uuid == ds['uuid']
