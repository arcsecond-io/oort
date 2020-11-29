import uuid
from unittest.mock import patch

import pytest
from arcsecond import ArcsecondAPI, ArcsecondError

from oort.cli.folders import parse_upload_watch_options, save_upload_folders
from oort.server.errors import InvalidAstronomerOortCloudError, InvalidOrganisationTelescopeOortCloudError
from oort.shared.config import get_config_upload_folder_sections
from tests.utils import (
    TEST_LOGIN_USERNAME,
    save_test_credentials,
    use_test_database
)


@use_test_database
def test_cli_folders_loggedin_astronomer_no_telescope():
    """Case of a single astronomer uploading for himself in a personal account,
    and not related to any telescope."""

    # Prepare
    save_test_credentials(subdomain=None)

    o, organisation, t, telescope = None, None, None, None
    astronomer = (None, None)

    # Perform
    username, api_key, org_subdomain, org_role, telescope_details = \
        parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

    # Assert
    assert username == TEST_LOGIN_USERNAME
    assert api_key == ''
    assert org_subdomain == ''
    assert org_role == ''
    assert telescope_details is None


@use_test_database
def test_cli_folders_loggedin_astronomer_with_t_option():
    """Case of a single astronomer uploading for himself in a personal account,
    but associated with a known telescope using the t option."""

    # Prepare
    save_test_credentials(subdomain=None)

    tel_uuid = str(uuid.uuid4())
    tel_details = {'uuid': tel_uuid, 'name': 'telescope name', 'coordinates': {}}

    o, organisation, t, telescope = None, None, tel_uuid, None
    astronomer = (None, None)

    with patch.object(ArcsecondAPI, 'read', return_value=(tel_details, None)) as mock_method_read:
        # Perform
        username, api_key, org_subdomain, org_role, telescope_details = \
            parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        # Assert
        assert mock_method_read.call_count == 1
        assert username == TEST_LOGIN_USERNAME
        assert api_key == ''
        assert org_subdomain == ''
        assert org_role == ''
        assert telescope_details == tel_details


@use_test_database
def test_cli_folders_loggedin_astronomer_with_telescope_option():
    """Case of a single astronomer uploading for himself in a personal account,
    but associated with a known telescope using the telescope option
    (instead of simply the t one)."""

    # Prepare
    save_test_credentials(subdomain=None)

    tel_uuid = str(uuid.uuid4())
    tel_details = {'uuid': tel_uuid, 'name': 'telescope name', 'coordinates': {}}

    o, organisation, t, telescope = None, None, None, tel_uuid
    astronomer = (None, None)

    with patch.object(ArcsecondAPI, 'read', return_value=(tel_details, None)) as mock_method_read:
        # Perform
        username, api_key, org_subdomain, org_role, telescope_details = \
            parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        # Assert
        assert mock_method_read.call_count == 1
        assert username == TEST_LOGIN_USERNAME
        assert api_key == ''
        assert org_subdomain == ''
        assert org_role == ''
        assert telescope_details == tel_details


@use_test_database
def test_cli_folders_loggedin_astronomer_with_telescope_option_but_invalid_telescope():
    """Case of a single astronomer uploading for himself in a personal account,
    but associated with a known telescope using the telescope option
    but the telescope is unknown."""

    # Prepare
    save_test_credentials(subdomain=None)

    tel_uuid = str(uuid.uuid4())

    o, organisation, t, telescope = None, None, None, tel_uuid
    astronomer = (None, None)

    with patch.object(ArcsecondAPI, 'read', return_value=(None, ArcsecondError())) as mock_method_read:
        # Perform
        with pytest.raises(InvalidOrganisationTelescopeOortCloudError):
            username, api_key, org_subdomain, org_role, telescope_details = \
                parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        # Assert
        assert mock_method_read.call_count == 1


@use_test_database
def test_cli_folders_custom_invalid_astronomer_no_telescope():
    """Case of a single astronomer uploading for a custom astronomer,
    and not related to any telescope."""

    # Prepare
    save_test_credentials(subdomain=None)

    o, organisation, t, telescope = None, None, None, None
    astronomer = ('custom', '1-2-3-4-5-6-7-8-9')

    with patch.object(ArcsecondAPI, 'me', return_value=ArcsecondAPI()) as mock_method_me, \
            patch.object(ArcsecondAPI, 'read', return_value=(None, ArcsecondError())) as mock_method_read:
        # Perform
        with pytest.raises(InvalidAstronomerOortCloudError):
            username, api_key, org_subdomain, org_role, telescope_details = \
                parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        # Assert
        assert mock_method_me.call_count == 1
        assert mock_method_me.call_args_list[0].kwargs == {'api_key': astronomer[1], 'debug': True, 'test': True}

        assert mock_method_read.call_count == 1
        assert mock_method_read.call_args_list[0].kwargs == {}
        assert mock_method_read.call_args_list[0].args == (astronomer[0],)


@use_test_database
def test_cli_folders_custom_valid_astronomer_no_telescope():
    """Case of a single astronomer uploading for a custom astronomer,
    and not related to any telescope."""

    # Prepare
    save_test_credentials(subdomain=None)

    o, organisation, t, telescope = None, None, None, None
    astronomer = ('custom', '1-2-3-4-5-6-7-8-9')
    astronomer_detail = {'username': astronomer[0]}

    with patch.object(ArcsecondAPI, 'me', return_value=ArcsecondAPI()) as mock_method_me, \
            patch.object(ArcsecondAPI, 'read', return_value=(astronomer_detail, None)) as mock_method_read:
        # Perform
        username, api_key, org_subdomain, org_role, telescope_details = \
            parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        # Assert
        assert mock_method_me.call_count == 1
        assert mock_method_me.call_args_list[0].kwargs == {'api_key': astronomer[1], 'debug': True, 'test': True}
        assert mock_method_read.call_count == 1
        assert mock_method_read.call_args_list[0].kwargs == {}
        assert mock_method_read.call_args_list[0].args == (astronomer[0],)

        assert username == astronomer[0]
        assert api_key == astronomer[1]
        assert org_subdomain == ''
        assert org_role == ''
        assert telescope_details is None

        folders = ['f1', 'f2']

        save_upload_folders(folders,
                            username,
                            api_key,
                            org_subdomain,
                            org_role,
                            telescope_details,
                            True)

        for folder_section in get_config_upload_folder_sections():
            assert folder_section.get('username', '') == username
            assert folder_section.get('api_key', '') == api_key
            assert folder_section.get('subdomain', '') == org_subdomain
            assert folder_section.get('role', '') == org_role
            assert folder_section.get('telescope', '') == telescope_details
