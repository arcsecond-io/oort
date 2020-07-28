import importlib
import os
from unittest.mock import patch

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
        assert mock_method.not_called()
