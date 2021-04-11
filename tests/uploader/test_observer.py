import threading
from unittest.mock import ANY, patch

from oort.shared.identity import Identity
from oort.uploader.engine.pathsobserver import PathsObserver
from tests.utils import use_test_database


def test_observer_empty():
    po = PathsObserver()
    assert po.observed_paths == []


@use_test_database
def test_observer_adding_folder_path():
    po = PathsObserver()
    with patch.object(PathsObserver, 'schedule', return_value={}) as mocked_method_schedule, \
            patch.object(PathsObserver, '_perform_initial_walk', return_value={}) as mocked_method_walk, \
            patch.object(threading.Timer, 'start'):
        po.observe_folder('.', Identity('cedric', '123', debug=True))
        mocked_method_walk.assert_called_once()
        mocked_method_schedule.assert_called_once_with(ANY, '.', recursive=True)
        assert po.observed_paths == ['.']
