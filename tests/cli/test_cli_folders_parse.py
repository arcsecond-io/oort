from unittest.mock import patch

import pytest
from arcsecond import ArcsecondAPI, ArcsecondError

from oort.cli.folders import parse_upload_watch_options
from oort.monitor.errors import (
    InvalidOrgMembershipOortCloudError,
    InvalidOrganisationTelescopeOortCloudError,
    InvalidTelescopeOortCloudError,
    InvalidWatchOptionsOortCloudError
)
from tests.utils import (ORG_DETAILS,
                         TEL_DETAILS,
                         TEL_UUID,
                         TEST_LOGIN_ORG_ROLE, TEST_LOGIN_ORG_SUBDOMAIN,
                         TEST_LOGIN_UPLOAD_KEY,
                         TEST_LOGIN_USERNAME,
                         clear_arcsecond_test_credentials,
                         clear_oort_test_folders,
                         save_arcsecond_test_credentials,
                         use_test_database)


@use_test_database
def test_cli_folders_no_options_not_logged_in():
    clear_oort_test_folders()
    clear_arcsecond_test_credentials()
    with pytest.raises(InvalidWatchOptionsOortCloudError):
        parse_upload_watch_options('', '', True, 'test')


@use_test_database
def test_cli_folders_no_options():
    # Prepare: Saving credentials for a single astronomer
    save_arcsecond_test_credentials(subdomain=None)
    clear_oort_test_folders()

    # Perform: Empty arguments everywhere
    identity = parse_upload_watch_options('', '', True, 'test')

    # Assert
    assert identity.username == TEST_LOGIN_USERNAME
    assert identity.upload_key == TEST_LOGIN_UPLOAD_KEY
    assert identity.subdomain == ''
    assert identity.role == ''
    assert identity.telescope_details is None


@use_test_database
def test_cli_folders_no_org_but_with_valid_telescope():
    save_arcsecond_test_credentials(subdomain=None)
    clear_oort_test_folders()

    with patch.object(ArcsecondAPI, 'read') as mock_method_read:
        mock_method_read.side_effect = [(TEL_DETAILS, None), ]
        identity = parse_upload_watch_options('', TEL_UUID, True, 'test')

        # Assert
        assert identity.username == TEST_LOGIN_USERNAME
        assert identity.upload_key == TEST_LOGIN_UPLOAD_KEY
        assert identity.subdomain == ''
        assert identity.role == ''
        assert identity.telescope_details == TEL_DETAILS


@use_test_database
def test_cli_folders_no_org_but_with_invalid_telescope():
    save_arcsecond_test_credentials(subdomain=None)
    clear_oort_test_folders()

    with patch.object(ArcsecondAPI, 'read', return_value=(None, ArcsecondError())) as mock_method_read:
        with pytest.raises(InvalidTelescopeOortCloudError):
            parse_upload_watch_options('', TEL_UUID, True, 'test')

        assert mock_method_read.call_count == 1


@use_test_database
def test_cli_folders_with_valid_org_but_not_member():
    clear_oort_test_folders()
    save_arcsecond_test_credentials(subdomain=None)

    with patch.object(ArcsecondAPI, 'read') as mock_method_read:
        mock_method_read.side_effect = [(ORG_DETAILS, None), (TEL_DETAILS, None)]

        with pytest.raises(InvalidOrgMembershipOortCloudError):
            parse_upload_watch_options(TEST_LOGIN_ORG_SUBDOMAIN, '', True, 'test')

        assert mock_method_read.call_count == 1


@use_test_database
def test_cli_folders_with_valid_org_and_valid_member_but_no_telescope():
    clear_oort_test_folders()
    save_arcsecond_test_credentials(subdomain=TEST_LOGIN_ORG_SUBDOMAIN)

    with patch.object(ArcsecondAPI, 'read', return_value=(ORG_DETAILS, None)) as mock_method_read, \
            patch.object(ArcsecondAPI, 'list', return_value=([TEL_DETAILS, ], None)) as mock_method_list:
        with pytest.raises(InvalidWatchOptionsOortCloudError):
            parse_upload_watch_options(TEST_LOGIN_ORG_SUBDOMAIN, '', True, 'test')

        assert mock_method_read.call_count == 1
        assert mock_method_list.call_count == 1


@use_test_database
def test_cli_folders_with_valid_org_and_valid_member_and_valid_telescope():
    clear_oort_test_folders()
    save_arcsecond_test_credentials(subdomain=TEST_LOGIN_ORG_SUBDOMAIN)

    with patch.object(ArcsecondAPI, 'read', return_value=(ORG_DETAILS, None)) as mock_method_read:
        mock_method_read.side_effect = [(ORG_DETAILS, None), (TEL_DETAILS, None)]
        identity = parse_upload_watch_options(TEST_LOGIN_ORG_SUBDOMAIN, TEL_UUID, True, 'test')

        # Assert
        assert identity.username == TEST_LOGIN_USERNAME
        assert identity.upload_key == TEST_LOGIN_UPLOAD_KEY
        assert identity.subdomain == TEST_LOGIN_ORG_SUBDOMAIN
        assert identity.role == TEST_LOGIN_ORG_ROLE
        assert identity.telescope_details == TEL_DETAILS


@use_test_database
def test_cli_folders_with_valid_org_and_valid_member_but_invalid_telescope():
    clear_oort_test_folders()
    save_arcsecond_test_credentials(subdomain=TEST_LOGIN_ORG_SUBDOMAIN)

    with patch.object(ArcsecondAPI, 'read') as mock_method_read:
        mock_method_read.side_effect = [(ORG_DETAILS, None), (None, ArcsecondError())]

        with pytest.raises(InvalidOrganisationTelescopeOortCloudError):
            parse_upload_watch_options(TEST_LOGIN_ORG_SUBDOMAIN, TEL_UUID, True, 'test')
