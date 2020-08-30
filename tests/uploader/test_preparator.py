import importlib
import os
import uuid
from unittest.mock import patch

from arcsecond.api.main import ArcsecondAPI

from oort.shared.identity import Identity
from oort.shared.models import Organisation
from oort.uploader.engine.packer import UploadPack
from oort.uploader.engine.preparator import UploadPreparator
from tests.utils import use_test_database

spec = importlib.util.find_spec('oort')

folder_path = os.path.join(os.path.dirname(spec.origin), '..', 'tests', 'fixtures')
fits_file_name = 'very_simple.fits'
fits_file_path = os.path.join(folder_path, fits_file_name)

telescope_uuid = '44f5bee9-a557-4264-86d6-c877d5013788'


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
    identity = Identity('cedric', str(uuid.uuid4()), 'saao', 'admin', telescope_uuid)
    pack = UploadPack(folder_path, fits_file_path, identity)
    with patch.object(UploadPreparator, 'prepare'), \
         patch.object(ArcsecondAPI, 'read', return_value=({'subdomain': 'saao'}, None)) as mock_method_read:
        assert Organisation.select().count() == 0
        prep = UploadPreparator(pack, identity)

        assert prep is not None
        assert prep.preparation_succeeded is False
        assert prep.telescope is None
        assert prep.night_log is None
        assert prep.obs_or_calib is None
        assert prep.dataset is None

        assert mock_method_read.called_once_with(date=pack.night_log_date_string)
        org = Organisation.select(Organisation.subdomain == 'saao').get()
        assert org is not None


@use_test_database
def test_preparator_prepare_no_org_no_telescope():
    identity = Identity('cedric', str(uuid.uuid4()), debug=True)
    pack = UploadPack(folder_path, fits_file_path, identity)
    assert len(pack.night_log_date_string) > 0
    assert identity.telescope is None

    nl = {'uuid': str(uuid.uuid4()), 'date': pack.night_log_date_string}
    obs = {'uuid': str(uuid.uuid4()), 'night_log': nl['uuid'], 'name': pack.dataset_name}
    ds = {'uuid': str(uuid.uuid4()), 'observation': obs['uuid'], 'name': pack.dataset_name}

    with patch.object(ArcsecondAPI, 'list', return_value=([], None)) as mock_method_list, \
            patch.object(ArcsecondAPI, 'create') as mock_method_create:
        mock_method_create.side_effect = [(nl, None), (obs, None), (ds, None)]

        up = UploadPreparator(pack, identity)
        up.prepare()
        assert mock_method_list.called_once_with(date=pack.night_log_date_string)
        assert mock_method_create.called_with(**nl)
        assert up.night_log is not None
        assert up.night_log.uuid == nl['uuid']

        assert mock_method_create.called_with(**obs)
        assert up.obs_or_calib is not None
        assert up.obs_or_calib.uuid == obs['uuid']

        assert mock_method_create.called_with(**ds)
        assert up.dataset is not None
        assert up.dataset.uuid == ds['uuid']
