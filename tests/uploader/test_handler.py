import importlib
import os
import time
import uuid
from unittest.mock import patch

from oort.shared.identity import Identity
from oort.uploader.engine.eventhandler import DataFileHandler
from tests.utils import use_test_database

spec = importlib.util.find_spec('oort')

folder_path = os.path.join(os.path.dirname(spec.origin), '..', 'tests', 'fixtures')
fits_file_name = 'very_simple.fits'
fits_file_path = os.path.join(folder_path, fits_file_name)

telescope_uuid = '44f5bee9-a557-4264-86d6-c877d5013788'


@use_test_database
def test_event_handler_simple_init():
    identity = Identity('cedric', str(uuid.uuid4()), 'saao', 'admin', telescope_uuid)

    with patch.object(DataFileHandler, '_restart_uploads') as mock_method:
        # To avoid a mock error:
        mock_method.__name__ = 'mock on_save_handler method'

        df = DataFileHandler(folder_path, identity, tick=0.1, debug=True)
        time.sleep(0.2)
        assert mock_method.call_count == 0


@use_test_database
def test_event_handler_init_followed_by_upload_restarts():
    identity = Identity('cedric', str(uuid.uuid4()), 'saao', 'admin', telescope_uuid)

    with patch.object(DataFileHandler, '_restart_uploads') as mock_method:
        # To avoid a mock error:
        mock_method.__name__ = 'mock on_save_handler method'

        df = DataFileHandler(folder_path, identity, tick=0.1, debug=True)
        df.launch_restart_loop()
        time.sleep(0.2)
        assert mock_method.call_count == 1
