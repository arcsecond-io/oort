import threading
from unittest.mock import ANY, patch

from oort.shared.identity import Identity
from oort.uploader.engine.pathsobserver import PathsObserver
from tests.utils import use_test_database


@use_test_database
def test_observer_empty():
    with patch.object(PathsObserver, 'schedule', return_value={}) as mocked_method_schedule, \
            patch.object(PathsObserver, '_start_initial_walk', return_value={}) as mocked_method_walk, \
            patch.object(threading.Thread, 'start'), \
            patch.object(threading.Timer, 'start'):
        po = PathsObserver()
        assert po.observed_paths == []
        mocked_method_schedule.assert_not_called()
        mocked_method_walk.assert_not_called()


@use_test_database
def test_observer_adding_folder_path():
    with patch.object(PathsObserver, 'schedule', return_value={}) as mocked_method_schedule, \
            patch.object(PathsObserver, '_start_initial_walk', return_value={}) as mocked_method_walk, \
            patch.object(threading.Timer, 'start'):
        po = PathsObserver()
        po._schedule_watch('.', Identity('cedric', '123', debug=True), True)
        mocked_method_walk.assert_called()
        mocked_method_schedule.assert_called_once_with(ANY, '.', recursive=True)
        assert po.observed_paths == ['.']
