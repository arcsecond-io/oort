import uuid
from unittest.mock import patch

from arcsecond import ArcsecondAPI
from arcsecond.config import (config_file_clear_section, config_file_save_api_key,
                              config_file_save_organisation_membership)
from click.testing import CliRunner

from oort.cli.cli import watch
from oort.server.errors import InvalidOrgMembershipOortCloudError, UnknownOrganisationOortCloudError
from oort.shared.models import Organisation
from tests.utils import use_test_database


def test_cli_watch_missing_folders():
    runner = CliRunner()
    result = runner.invoke(watch)
    assert result.exit_code != 0 and result.exception
    assert 'Missing argument \'FOLDERS...\'' in result.output


def test_cli_watch_unknown_organisation():
    runner = CliRunner()
    error = {'detail': 'unknown organisation'}
    with patch.object(ArcsecondAPI, 'read', return_value=(None, error)) as mock_method_read:
        result = runner.invoke(watch, ['.', '-o', 'dummy_org'])
        assert result.exit_code != 0
        assert isinstance(result.exception, UnknownOrganisationOortCloudError)
        mock_method_read.assert_called_once_with('dummy_org')


@use_test_database
def test_cli_watch_unknown_membership():
    config_file_clear_section('test')
    runner = CliRunner()
    # Create the watch command org to pass the org check.
    Organisation.smart_create(subdomain='robotland')
    # Configure an account but for a different org.
    config_file_save_api_key('1234567890', 'cedric', section='test')
    config_file_save_organisation_membership('saao', 'admin', section='test')
    # Make the test
    result = runner.invoke(watch, ['.', '-o', 'robotland'])
    assert result.exit_code != 0
    assert isinstance(result.exception, InvalidOrgMembershipOortCloudError)


@use_test_database
def test_cli_watch_missing_org_telescope():
    config_file_clear_section('test')
    runner = CliRunner()
    # Create the watch command org to pass the org check.
    Organisation.smart_create(subdomain='robotland')
    # Configure an account but for a different org.
    config_file_save_api_key('1234567890', 'cedric', section='test')
    config_file_save_organisation_membership('robotland', 'admin', section='test')
    # Make the test
    with patch.object(ArcsecondAPI, 'list', return_value=([], None)) as mock_method_read:
        result = runner.invoke(watch, ['.', '-o', 'robotland'])
        assert result.exit_code == 0
        assert "Here is a list of existing telescopes for organisation robotland:" in result.output
        mock_method_read.assert_called_once()


@use_test_database
def test_cli_watch_with_org_telescope():
    config_file_clear_section('test')
    runner = CliRunner()
    # Create the watch command org to pass the org check.
    Organisation.smart_create(subdomain='robotland')
    # Configure an account but for a different org.
    config_file_save_api_key('1234567890', 'cedric', section='test')
    config_file_save_organisation_membership('robotland', 'admin', section='test')
    # Make the test
    telescope_uuid = str(uuid.uuid4())
    telescope_details = {'uuid': telescope_uuid, 'name': 'telescope name', 'coordinates': {}}
    with patch.object(ArcsecondAPI, 'read', return_value=(telescope_details, None)) as mock_method_read, \
            patch('builtins.input', return_value='Nope'):
        result = runner.invoke(watch, ['.', '-o', 'robotland', '-t', telescope_uuid])
        assert result.exit_code == 0
        assert 'account username: @cedric' in result.output.lower()
        assert 'uploading for organisation: robotland' in result.output.lower()
        mock_method_read.assert_called_once()
