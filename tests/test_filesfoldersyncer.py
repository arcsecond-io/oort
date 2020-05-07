import os
from unittest.mock import patch
from arcsecond.api.main import ArcsecondAPI

from oort.app.helpers.filesfoldersyncer import FilesFolderSyncer
from oort.app.helpers.context import Context

from tests.utils import register_successful_personal_login


def get_syncer():
    register_successful_personal_login()
    folder = os.path.abspath(__file__)
    config = {'debug': True, 'verbose': True, 'folder': folder, 'organisation': None}
    return FilesFolderSyncer(Context(config), None, folder)


def test_resource_name_check_valid_current_name():
    ffs = get_syncer()
    resource = {'name': 'a dummy name'}
    updated_resource = ffs._check_resource_name(None, resource, 'A new name')
    assert updated_resource.get('name') == resource.get('name')


def test_resource_name_check_empty_current_name():
    ffs = get_syncer()
    kwargs_name = 'A new name'
    resource = {'name': '', 'uuid': '1-2-3-4-5'}
    new_resource = {'name': kwargs_name, 'uuid': '1-2-3-4-5'}
    with patch.object(ArcsecondAPI, 'update', return_value=(new_resource, None)) as mock_method:
        api = ArcsecondAPI()
        updated_resource = ffs._check_resource_name(api, resource, kwargs_name)
        assert updated_resource.get('name') == kwargs_name
        mock_method.assert_called_once_with(resource.get('uuid'), {'name': kwargs_name})
