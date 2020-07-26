from unittest.mock import ANY, patch

from oort.uploader.engine.eventhandler import DataFileHandler
from oort.uploader.engine.pathsobserver import PathsObserver


def test_observer_empty():
    po = PathsObserver()
    assert po.observed_paths == []


def test_observer_adding_folder_path():
    po = PathsObserver()
    with patch.object(DataFileHandler, 'run_initial_walk'), \
         patch.object(PathsObserver, 'schedule') as mocked_method:
        po.start_observe_folder('.', None)
        assert mocked_method.called_once_with(ANY, '.', recursive=True)
        assert po.observed_paths == ['.']
