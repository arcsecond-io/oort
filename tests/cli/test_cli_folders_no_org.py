from unittest.mock import patch

import pytest
from arcsecond import ArcsecondAPI, ArcsecondError

from oort.cli.folders import parse_upload_watch_options
from oort.server.errors import (
    InvalidOrgMembershipOortCloudError,
    InvalidOrganisationTelescopeOortCloudError,
    InvalidWatchOptionsOortCloudError
)
from tests.utils import (CUSTOM_ASTRONOMER,
                         CUSTOM_ASTRONOMER_DETAILS,
                         ORG_DETAILS,
                         TEL_DETAILS,
                         TEL_UUID,
                         TEST_LOGIN_ORG_SUBDOMAIN,
                         TEST_LOGIN_UPLOAD_KEY,
                         TEST_LOGIN_USERNAME,
                         save_test_credentials,
                         use_test_database)


@use_test_database
def test_cli_folders_no_options_org_nor_telescope():
    """Case of a single astronomer uploading for himself in a personal account,
    and not related to any telescope."""

    # Prepare: Saving credentials for a single astronomer
    save_test_credentials(subdomain=None)

    # Perform: Empty arguments everywhere
    organisation, telescope, astronomer = None, None, (None, None)
    username, upload_key, org_subdomain, org_role, telescope_details = \
        parse_upload_watch_options(organisation, telescope, astronomer, True)

    # Assert
    assert username == TEST_LOGIN_USERNAME
    assert upload_key == TEST_LOGIN_UPLOAD_KEY
    assert org_subdomain == ''
    assert org_role == ''
    assert telescope_details is None


@use_test_database
def test_cli_folders_with_options_org_but_no_telescope():
    """Case of a single astronomer uploading for himself in a personal account,
    and not related to any telescope."""

    # Prepare: Saving credentials for a single astronomer
    save_test_credentials(subdomain=None)

    with patch.object(ArcsecondAPI, 'read', return_value=(ORG_DETAILS, None)) as mock_method_read:
        with pytest.raises(InvalidOrgMembershipOortCloudError):
            # Perform: Empty arguments everywhere except organisation
            organisation, telescope, astronomer = TEST_LOGIN_ORG_SUBDOMAIN, None, (None, None)
            username, upload_key, org_subdomain, org_role, telescope_details = \
                parse_upload_watch_options(organisation, telescope, astronomer, True)

        assert mock_method_read.call_count == 1


@use_test_database
def test_cli_folders_with_options_org_and_telescope():
    """Case of a single astronomer uploading for himself in a personal account,
    and not related to any telescope."""

    # Prepare: Saving credentials for a single astronomer
    save_test_credentials(subdomain=None)

    with patch.object(ArcsecondAPI, 'read', return_value=(ORG_DETAILS, None)) as mock_method_read:
        with pytest.raises(InvalidOrgMembershipOortCloudError):
            # Perform: Empty arguments everywhere except organisation
            organisation, telescope, astronomer = TEST_LOGIN_ORG_SUBDOMAIN, TEL_UUID, (None, None)
            username, upload_key, org_subdomain, org_role, telescope_details = \
                parse_upload_watch_options(organisation, telescope, astronomer, True)

        assert mock_method_read.call_count == 1


@use_test_database
def test_cli_folders_with_options_telescope():
    """Case of a single astronomer uploading for himself in a personal account,
    but associated with a known telescope using the t option."""

    # Prepare
    save_test_credentials(subdomain=None)

    with patch.object(ArcsecondAPI, 'read', return_value=(TEL_DETAILS, None)) as mock_method_read:
        # Perform
        organisation, telescope, astronomer = None, TEL_UUID, (None, None)
        username, upload_key, org_subdomain, org_role, telescope_details = \
            parse_upload_watch_options(organisation, telescope, astronomer, True)

        # Assert
        assert mock_method_read.call_count == 1
        assert username == TEST_LOGIN_USERNAME
        assert upload_key == TEST_LOGIN_UPLOAD_KEY
        assert org_subdomain == ''
        assert org_role == ''
        assert telescope_details == TEL_DETAILS


@use_test_database
def test_cli_folders_with_options_telescope_but_invalid_telescope():
    """Case of a single astronomer uploading for himself in a personal account,
    but associated with a known telescope using the telescope option
    but the telescope is unknown."""

    save_test_credentials(subdomain=None)

    with patch.object(ArcsecondAPI, 'read', return_value=(None, ArcsecondError())) as mock_method_read:
        with pytest.raises(InvalidOrganisationTelescopeOortCloudError):
            # The value of TEL_UUID has no importance, as method is patched.
            organisation, telescope, astronomer = None, TEL_UUID, (None, None)
            username, upload_key, org_subdomain, org_role, telescope_details = \
                parse_upload_watch_options(organisation, telescope, astronomer, True)

        assert mock_method_read.call_count == 1


@use_test_database
def test_cli_folders_with_options_custom_astronomer_but_no_org_nor_telescope():
    save_test_credentials(subdomain=None)

    with patch.object(ArcsecondAPI, 'me', return_value=ArcsecondAPI(test=True)) as mock_method_me, \
            patch.object(ArcsecondAPI, 'read', return_value=(CUSTOM_ASTRONOMER_DETAILS, None)) as mock_method_read:
        with pytest.raises(InvalidWatchOptionsOortCloudError):
            organisation, telescope, astronomer = None, None, CUSTOM_ASTRONOMER
            username, upload_key, org_subdomain, org_role, telescope_details = \
                parse_upload_watch_options(organisation, telescope, astronomer, True)

        assert mock_method_me.call_count == 1
        assert mock_method_read.call_count == 1


@use_test_database
def test_cli_folders_with_options_custom_astronomer_with_org_but_no_telescope():
    save_test_credentials(subdomain=None)

    with patch.object(ArcsecondAPI, 'me', return_value=ArcsecondAPI(test=True)) as mock_method_me, \
            patch.object(ArcsecondAPI, 'read', return_value=(CUSTOM_ASTRONOMER_DETAILS, None)) as mock_method_read:
        with pytest.raises(InvalidOrgMembershipOortCloudError):
            organisation, telescope, astronomer = TEST_LOGIN_ORG_SUBDOMAIN, None, CUSTOM_ASTRONOMER
            username, upload_key, org_subdomain, org_role, telescope_details = \
                parse_upload_watch_options(organisation, telescope, astronomer, True)

        assert mock_method_me.call_count == 0
        assert mock_method_read.call_count == 1


@use_test_database
def test_cli_folders_with_options_custom_astronomer_with_org_and_telescope():
    save_test_credentials(subdomain=None)

    with patch.object(ArcsecondAPI, 'me', return_value=ArcsecondAPI(test=True)) as mock_method_me, \
            patch.object(ArcsecondAPI, 'read', return_value=(CUSTOM_ASTRONOMER_DETAILS, None)) as mock_method_read:
        with pytest.raises(InvalidOrgMembershipOortCloudError):
            organisation, telescope, astronomer = TEST_LOGIN_ORG_SUBDOMAIN, TEL_UUID, CUSTOM_ASTRONOMER
            username, upload_key, org_subdomain, org_role, telescope_details = \
                parse_upload_watch_options(organisation, telescope, astronomer, True)

        assert mock_method_me.call_count == 0
        assert mock_method_read.call_count == 1
