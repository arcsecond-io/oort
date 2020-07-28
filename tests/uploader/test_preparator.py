import importlib
import os
import uuid
from unittest.mock import patch

import pytest
from arcsecond import Arcsecond

from oort.shared.identity import Identity
from oort.uploader.engine.packer import UploadPack
from oort.uploader.engine.preparator import UploadPreparator

spec = importlib.util.find_spec('oort')
fits_file_path = os.path.join(os.path.dirname(spec.origin), '..', 'tests', 'fixtures', 'very_simple.fits')


def test_preparator_init():
    pack = UploadPack('.', fits_file_path)
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
async def test_preparator_prepare_no_org_no_telescope():
    pack = UploadPack('.', fits_file_path)
    assert len(pack.night_log_date_string) > 0

    with patch.object(Arcsecond, 'build_nightlogs_api') as mock_method:
        up = UploadPreparator(pack, Identity('cedric', str(uuid.uuid4()), debug=True))
        await up.prepare()
        assert mock_method.called_once()
