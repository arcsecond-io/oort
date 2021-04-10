import uuid
from unittest.mock import patch

import pytest
from arcsecond import ArcsecondAPI, ArcsecondError

from oort.cli.folders import parse_upload_watch_options
from oort.server.errors import (
    InvalidOrgMembershipOortCloudError,
    InvalidOrganisationTelescopeOortCloudError,
    InvalidWatchOptionsOortCloudError
)
from tests.utils import (TEST_LOGIN_API_KEY, TEST_LOGIN_ORG_ROLE, TEST_LOGIN_ORG_SUBDOMAIN, TEST_LOGIN_USERNAME,
                         save_test_credentials, use_test_database)

TELESCOPE_UUID = str(uuid.uuid4())
TELESCOPE_DETAILS = {'uuid': TELESCOPE_UUID, 'name': 'telescope name', 'coordinates': {}}
ORG_DETAILS = {'subdomain': TEST_LOGIN_ORG_SUBDOMAIN}
ORG_MEMBERSHIPS = {TEST_LOGIN_ORG_SUBDOMAIN: TEST_LOGIN_ORG_ROLE}
CUSTOM_ASTRONOMER = ('custom', '1-2-3-4-5-6-7-8-9')
CUSTOM_ASTRONOMER_DETAILS = {'username': CUSTOM_ASTRONOMER[0], 'key': CUSTOM_ASTRONOMER[1]}


@use_test_database
def test_cli_folders_no_options_org_nor_telescope():
    """Case of a single astronomer uploading for himself in a personal account,
    and not related to any telescope."""

    # Prepare: Saving credentials for a single astronomer
    save_test_credentials(subdomain=None)

    # Perform: Empty arguments everywhere
    o, organisation, t, telescope, astronomer = None, None, None, None, (None, None)
    username, api_key, org_subdomain, org_role, telescope_details = \
        parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

    # Assert
    assert username == TEST_LOGIN_USERNAME
    assert api_key == TEST_LOGIN_API_KEY
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
            o, organisation, t, telescope, astronomer = TEST_LOGIN_ORG_SUBDOMAIN, None, None, None, (None, None)
            username, api_key, org_subdomain, org_role, telescope_details = \
                parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

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
            o, organisation, t, telescope, astronomer = TEST_LOGIN_ORG_SUBDOMAIN, None, TELESCOPE_UUID, None, (
                None, None)
            username, api_key, org_subdomain, org_role, telescope_details = \
                parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        assert mock_method_read.call_count == 1


@use_test_database
def test_cli_folders_with_options_telescope_as_t():
    """Case of a single astronomer uploading for himself in a personal account,
    but associated with a known telescope using the t option."""

    # Prepare
    save_test_credentials(subdomain=None)

    with patch.object(ArcsecondAPI, 'read', return_value=(TELESCOPE_DETAILS, None)) as mock_method_read:
        # Perform
        o, organisation, t, telescope, astronomer = None, None, TELESCOPE_UUID, None, (None, None)
        username, api_key, org_subdomain, org_role, telescope_details = \
            parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        # Assert
        assert mock_method_read.call_count == 1
        assert username == TEST_LOGIN_USERNAME
        assert api_key == TEST_LOGIN_API_KEY
        assert org_subdomain == ''
        assert org_role == ''
        assert telescope_details == TELESCOPE_DETAILS


@use_test_database
def test_cli_folders_with_options_telescope_as_telescope():
    """Case of a single astronomer uploading for himself in a personal account,
    but associated with a known telescope using the telescope option
    (instead of simply the t one)."""

    save_test_credentials(subdomain=None)

    with patch.object(ArcsecondAPI, 'read', return_value=(TELESCOPE_DETAILS, None)) as mock_method_read:
        o, organisation, t, telescope, astronomer = None, None, None, TELESCOPE_UUID, (None, None)
        username, api_key, org_subdomain, org_role, telescope_details = \
            parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        # Assert
        assert mock_method_read.call_count == 1
        assert username == TEST_LOGIN_USERNAME
        assert api_key == TEST_LOGIN_API_KEY
        assert org_subdomain == ''
        assert org_role == ''
        assert telescope_details == TELESCOPE_DETAILS


@use_test_database
def test_cli_folders_with_options_telescope_but_invalid_telescope():
    """Case of a single astronomer uploading for himself in a personal account,
    but associated with a known telescope using the telescope option
    but the telescope is unknown."""

    save_test_credentials(subdomain=None)

    with patch.object(ArcsecondAPI, 'read', return_value=(None, ArcsecondError())) as mock_method_read:
        with pytest.raises(InvalidOrganisationTelescopeOortCloudError):
            # The value of TELESCOPE_UUID has no importance, as method is patched.
            o, organisation, t, telescope, astronomer = None, None, None, TELESCOPE_UUID, (None, None)
            username, api_key, org_subdomain, org_role, telescope_details = \
                parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        assert mock_method_read.call_count == 1


@use_test_database
def test_cli_folders_with_options_custom_astronomer_but_no_org_nor_telescope():
    save_test_credentials(subdomain=None)

    with patch.object(ArcsecondAPI, 'me', return_value=ArcsecondAPI(test=True)) as mock_method_me, \
            patch.object(ArcsecondAPI, 'read', return_value=(CUSTOM_ASTRONOMER_DETAILS, None)) as mock_method_read:
        with pytest.raises(InvalidWatchOptionsOortCloudError):
            o, organisation, t, telescope, astronomer = None, None, None, None, CUSTOM_ASTRONOMER
            username, api_key, org_subdomain, org_role, telescope_details = \
                parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        assert mock_method_me.call_count == 1
        assert mock_method_read.call_count == 1


@use_test_database
def test_cli_folders_with_options_custom_astronomer_with_org_but_no_telescope():
    save_test_credentials(subdomain=None)

    with patch.object(ArcsecondAPI, 'me', return_value=ArcsecondAPI(test=True)) as mock_method_me, \
            patch.object(ArcsecondAPI, 'read', return_value=(CUSTOM_ASTRONOMER_DETAILS, None)) as mock_method_read:
        with pytest.raises(InvalidOrgMembershipOortCloudError):
            o, organisation, t, telescope, astronomer = TEST_LOGIN_ORG_SUBDOMAIN, None, None, None, CUSTOM_ASTRONOMER
            username, api_key, org_subdomain, org_role, telescope_details = \
                parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        assert mock_method_me.call_count == 0
        assert mock_method_read.call_count == 1


@use_test_database
def test_cli_folders_with_options_custom_astronomer_with_org_and_telescope():
    save_test_credentials(subdomain=None)

    with patch.object(ArcsecondAPI, 'me', return_value=ArcsecondAPI(test=True)) as mock_method_me, \
            patch.object(ArcsecondAPI, 'read', return_value=(CUSTOM_ASTRONOMER_DETAILS, None)) as mock_method_read:
        with pytest.raises(InvalidOrgMembershipOortCloudError):
            o, organisation, t, telescope, astronomer = TEST_LOGIN_ORG_SUBDOMAIN, None, TELESCOPE_UUID, None, CUSTOM_ASTRONOMER
            username, api_key, org_subdomain, org_role, telescope_details = \
                parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        assert mock_method_me.call_count == 0
        assert mock_method_read.call_count == 1
