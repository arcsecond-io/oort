import importlib
import inspect
import os
import sys
import uuid
from functools import wraps
from unittest.mock import patch

import peewee
import pytest
from arcsecond.api.main import ArcsecondAPI

from oort.shared.identity import Identity
from oort.shared.models import BaseModel
from oort.uploader.engine.packer import UploadPack
from oort.uploader.engine.preparator import UploadPreparator

spec = importlib.util.find_spec('oort')

folder_path = os.path.join(os.path.dirname(spec.origin), '..', 'tests', 'fixtures')
fits_file_path = os.path.join(folder_path, 'very_simple.fits')

MODELS = [m[1] for m in inspect.getmembers(sys.modules['oort.shared.models'], inspect.isclass) if
          issubclass(m[1], peewee.Model) and m[1] != peewee.Model and m[1] != BaseModel]


def use_test_database(fn):
    test_db = peewee.SqliteDatabase(':memory:')

    @wraps(fn)
    async def inner():
        with test_db.bind_ctx(MODELS):
            test_db.create_tables(MODELS)
            try:
                await fn()
            finally:
                test_db.drop_tables(MODELS)

    return inner


def test_preparator_init():
    pack = UploadPack(folder_path, fits_file_path)
    with patch.object(UploadPreparator, 'prepare') as mock_method:
        up = UploadPreparator(pack, Identity('cedric', str(uuid.uuid4()), debug=True))
        assert up is not None
        assert up.preparation_succeeded is False
        assert up.telescope is None
        assert up.night_log is None
        assert up.obs_or_calib is None
        assert up.dataset is None
        assert mock_method.not_called()


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
        assert up.night_log == nl
        assert mock_method_create.called_with(**obs)
        assert up.obs_or_calib == obs
        assert mock_method_create.called_with(**ds)
        assert up.dataset == ds
