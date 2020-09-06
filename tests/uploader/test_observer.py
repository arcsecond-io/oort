from unittest.mock import ANY, patch

from oort.shared.identity import Identity
from oort.uploader.engine.pathsobserver import PathsObserver


def test_observer_empty():
    po = PathsObserver()
    assert po.observed_paths == []


def test_observer_adding_folder_path():
    po = PathsObserver()
    with patch.object(PathsObserver, 'schedule') as mocked_method:
        po.observe_folder('.', Identity('cedric', '123', debug=True))
        mocked_method.assert_called_once_with(ANY, '.', recursive=True)
        assert po.observed_paths == ['.']
