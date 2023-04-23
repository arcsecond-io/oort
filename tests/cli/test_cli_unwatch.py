import re
import uuid
from unittest.mock import patch

from arcsecond import ArcsecondAPI
from click.testing import CliRunner

from oort.cli.cli import unwatch, watch, folders
from oort.shared.models import Organisation
from tests.utils import TEST_LOGIN_ORG_SUBDOMAIN, save_arcsecond_test_credentials, use_test_database


@use_test_database
def test_cli_unwatch_no_folders():
    save_arcsecond_test_credentials()
    runner = CliRunner()
    result = runner.invoke(unwatch)
    assert result.exit_code != 0 and result.exception
    assert 'Missing argument \'FOLDER_ID...\'' in result.output


@use_test_database
def test_cli_unwatch_one_valid_folder_no_org():
    runner = CliRunner()
    with patch('builtins.input', return_value='\n'):
        runner.invoke(watch, ['.', '--api', 'test'])

    result = runner.invoke(folders)
    folder_id = re.match('.*(?P<folder_id>[a-z0-9]{6}-tests).*', result.output).group('folder_id')
    result = runner.invoke(unwatch, [folder_id])
    assert result.exit_code == 0
    assert f' • Folder ID {folder_id} removed with success: True.' in result.output


@use_test_database
def test_cli_unwatch_one_valid_folder_with_org():
    Organisation.create(subdomain=TEST_LOGIN_ORG_SUBDOMAIN)
    runner = CliRunner()
    telescope_uuid = str(uuid.uuid4())
    telescope_details = {'uuid': telescope_uuid, 'name': 'telescope name', 'coordinates': {}}

    with patch.object(ArcsecondAPI, 'read', return_value=(telescope_details, None)), \
            patch('builtins.input', return_value='\n'):
        runner.invoke(watch, ['.', '-o', TEST_LOGIN_ORG_SUBDOMAIN, '-t', telescope_uuid, '--api', 'test'])

    result = runner.invoke(folders)
    folder_id = re.match('.*(?P<folder_id>[a-z0-9]{6}-tests).*', result.output).group('folder_id')
    result = runner.invoke(unwatch, [folder_id])
    assert result.exit_code == 0
    assert f' • Folder ID {folder_id} removed with success: True.' in result.output
