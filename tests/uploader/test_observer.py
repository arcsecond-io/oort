import threading
from unittest.mock import ANY, patch

from oort.shared.identity import Identity
from oort.shared.models import Upload
from oort.uploader.engine.pathsobserver import PathObserver, PathObserverManager
from tests.utils import use_test_database


@use_test_database
def test_observer_manager_empty():
    with patch.object(PathObserverManager, '_detect_watched_folders', return_value={}) as mocked_method_walk:
        pom = PathObserverManager()
        assert pom.observed_paths == []
        mocked_method_walk.assert_not_called()


# @use_test_database
# def test_observer_adding_folder_path():
#     with patch.object(Upload, 'is_finished', return_value=False), \
#             patch.object(threading.Timer, 'start'):
#         po = PathObserver('.', Identity('cedric', '123', debug=True), True)
#         po.prepare()
#         mocked_method_walk.assert_called()
#         mocked_method_schedule.assert_called_once_with(ANY, '.', recursive=True)
#         assert po.observed_paths == ['.']
