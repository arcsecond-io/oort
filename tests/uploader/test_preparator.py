import importlib
import os
import uuid
from unittest.mock import patch

import pytest
from arcsecond.api.main import ArcsecondAPI

from oort.shared.identity import Identity
from oort.shared.models import Organisation
from oort.uploader.engine.packer import UploadPack
from oort.uploader.engine.preparator import UploadPreparator
from tests.utils import use_test_database

spec = importlib.util.find_spec('oort')

folder_path = os.path.join(os.path.dirname(spec.origin), '..', 'tests', 'fixtures')
fits_file_path = os.path.join(folder_path, 'very_simple.fits')


@pytest.mark.asyncio
@use_test_database
async def test_preparator_init_no_org():
    pack = UploadPack(folder_path, fits_file_path)
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


@pytest.mark.asyncio
@use_test_database
async def test_preparator_init_with_org():
    pack = UploadPack(folder_path, fits_file_path)
    telescope_uuid = '44f5bee9-a557-4264-86d6-c877d5013788'
    identity = Identity('cedric', str(uuid.uuid4()), 'saao', 'admin', telescope_uuid)
    with patch.object(UploadPreparator, 'prepare') as mock_method:
        assert Organisation.select().count() == 0
        prep = UploadPreparator(pack, identity)
        assert prep is not None
        assert prep.preparation_succeeded is False
        assert prep.telescope is None
        assert prep.night_log is None
        assert prep.obs_or_calib is None
        assert prep.dataset is None
        org = Organisation.select(Organisation.subdomain == 'saao').get()
        assert org is not None


@pytest.mark.asyncio
@use_test_database
async def test_preparator_prepare_no_org_no_telescope():
    pack = UploadPack(folder_path, fits_file_path)
    identity = Identity('cedric', str(uuid.uuid4()), debug=True)
    assert len(pack.night_log_date_string) > 0
    assert identity.telescope is None

    nl = {'uuid': str(uuid.uuid4()), 'date': pack.night_log_date_string}
    obs = {'uuid': str(uuid.uuid4()), 'night_log': nl['uuid'], 'name': 'observation!'}
    ds = {'uuid': str(uuid.uuid4()), 'observation': obs['uuid'], 'name': 'dataset!'}

    with patch.object(ArcsecondAPI, 'list', return_value=([], None)) as mock_method_list, \
            patch.object(ArcsecondAPI, 'create') as mock_method_create:
        mock_method_create.side_effect = [(nl, None), (obs, None), (ds, None)]

        up = UploadPreparator(pack, identity)
        await up.prepare()
        assert mock_method_list.called_once_with(date=pack.night_log_date_string)
        assert mock_method_create.called_with(**nl)
        assert up.night_log.uuid == nl['uuid']
        assert mock_method_create.called_with(**obs)
        assert up.obs_or_calib.uuid == obs['uuid']
        assert mock_method_create.called_with(**ds)
        assert up.dataset.uuid == ds['uuid']
