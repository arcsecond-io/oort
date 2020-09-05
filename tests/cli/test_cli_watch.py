import uuid
from unittest.mock import patch

from arcsecond import ArcsecondAPI
from arcsecond.config import config_file_save_api_key, config_file_save_organisation_membership
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
        assert mock_method_read.called_once_with(organisation='dummy_org')


@use_test_database
def test_cli_watch_unknown_membership():
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
