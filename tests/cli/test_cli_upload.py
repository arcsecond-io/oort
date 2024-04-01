from unittest.mock import patch

from arcsecond import ArcsecondAPI
from click.testing import CliRunner

from oort.cli.cli import upload
from oort.cli.errors import UnknownOrganisationOortCloudError
from tests.utils import save_arcsecond_test_credentials


def test_cli_upload_missing_folders():
    save_arcsecond_test_credentials()
    runner = CliRunner()
    result = runner.invoke(upload)
    assert result.exit_code != 0 and result.exception
    assert 'Missing argument \'FOLDER\'.' in result.output


def test_cli_upload_unknown_organisation():
    save_arcsecond_test_credentials()
    runner = CliRunner()
    error = {'detail': 'unknown organisation'}
    with patch.object(ArcsecondAPI, 'read', return_value=(None, error)) as mock_method_read:
        result = runner.invoke(upload, ['.', '-d', 'ds1', '-o', 'dummy_org', '--api', 'test'])
        assert result.exit_code != 0
        assert isinstance(result.exception, UnknownOrganisationOortCloudError)
        mock_method_read.assert_called_once_with('dummy_org')

#
# def test_cli_upload_unknown_membership():
#     save_arcsecond_test_credentials(subdomain=TEST_LOGIN_ORG_SUBDOMAIN)
#     # Make the test
#     runner = CliRunner()
#     result = runner.invoke(upload, ['.', '-d', 'ds1', '-o', TEST_LOGIN_ORG_SUBDOMAIN, '--api', 'test'])
#     assert result.exit_code != 0
#     assert isinstance(result.exception, InvalidOrgMembershipOortCloudError)
