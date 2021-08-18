import uuid
from unittest.mock import patch

from arcsecond import ArcsecondAPI
from click.testing import CliRunner

from oort.cli.cli import watch
from oort.server.errors import InvalidOrgMembershipOortCloudError, UnknownOrganisationOortCloudError
from oort.shared.models import Organisation
from tests.utils import TEST_LOGIN_ORG_SUBDOMAIN, TEST_LOGIN_USERNAME, save_arcsecond_test_credentials, use_test_database


@use_test_database
def test_cli_watch_missing_folders():
    save_arcsecond_test_credentials()
    runner = CliRunner()
    result = runner.invoke(watch)
    assert result.exit_code != 0 and result.exception
    assert 'Missing argument \'FOLDERS...\'' in result.output


@use_test_database
def test_cli_watch_unknown_organisation():
    save_arcsecond_test_credentials()
    runner = CliRunner()
    error = {'detail': 'unknown organisation'}
    with patch.object(ArcsecondAPI, 'read', return_value=(None, error)) as mock_method_read:
        result = runner.invoke(watch, ['.', '-o', 'dummy_org'])
        assert result.exit_code != 0
        assert isinstance(result.exception, UnknownOrganisationOortCloudError)
        mock_method_read.assert_called_once_with('dummy_org')


@use_test_database
def test_cli_watch_unknown_membership():
    save_arcsecond_test_credentials(subdomain='saao')
    Organisation.create(subdomain='saao')
    Organisation.create(subdomain=TEST_LOGIN_ORG_SUBDOMAIN)
    # Make the test
    runner = CliRunner()
    result = runner.invoke(watch, ['.', '-o', TEST_LOGIN_ORG_SUBDOMAIN])
    assert result.exit_code != 0
    assert isinstance(result.exception, InvalidOrgMembershipOortCloudError)


@use_test_database
def test_cli_watch_missing_org_telescope():
    save_arcsecond_test_credentials()
    # Create the watch command org to pass the org check.
    Organisation.create(subdomain=TEST_LOGIN_ORG_SUBDOMAIN)
    # Make the test
    runner = CliRunner()
    with patch.object(ArcsecondAPI, 'list', return_value=([], None)) as mock_method_read:
        result = runner.invoke(watch, ['.', '-o', TEST_LOGIN_ORG_SUBDOMAIN])
        assert result.exit_code == 0
        assert f"Here is a list of existing telescopes for organisation {TEST_LOGIN_ORG_SUBDOMAIN}:" in result.output
        mock_method_read.assert_called_once()


@use_test_database
def test_cli_watch_with_org_telescope():
    # Prepare
    save_arcsecond_test_credentials()
    Organisation.create(subdomain=TEST_LOGIN_ORG_SUBDOMAIN)
    runner = CliRunner()
    telescope_uuid = str(uuid.uuid4())
    telescope_details = {'uuid': telescope_uuid, 'name': 'telescope name', 'coordinates': {}}

    # Run
    with patch.object(ArcsecondAPI, 'read', return_value=(telescope_details, None)) as mock_method_read, \
            patch('builtins.input', return_value='Nope'):
        result = runner.invoke(watch, ['.', '-o', TEST_LOGIN_ORG_SUBDOMAIN, '-t', telescope_uuid])

        # Assert
        assert result.exit_code == 0
        assert f"arcsecond username: @{TEST_LOGIN_USERNAME}" in result.output.lower()
        assert f"uploading to organisation account '{TEST_LOGIN_ORG_SUBDOMAIN}'" in result.output.lower()
        mock_method_read.assert_called_once()
