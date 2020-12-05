import uuid
from unittest.mock import patch

import pytest
from arcsecond import ArcsecondAPI, ArcsecondError

from oort.cli.folders import parse_upload_watch_options, save_upload_folders
from oort.server.errors import InvalidOrganisationTelescopeOortCloudError, InvalidWatchOptionsOortCloudError
from oort.shared.config import get_config_upload_folder_sections
from oort.shared.identity import Identity
from tests.utils import (
    TEST_LOGIN_ORG_ROLE,
    TEST_LOGIN_ORG_SUBDOMAIN,
    TEST_LOGIN_USERNAME,
    save_test_credentials,
    use_test_database
)


@use_test_database
def test_cli_folders_loggedin_astronomer_with_o_option_no_telescope():
    """Case of an astronomer logged in and uploading for an organisation account.
    A telescope must be provided."""

    # Prepare
    save_test_credentials()
    org_details = {'subdomain': TEST_LOGIN_ORG_SUBDOMAIN}

    o, organisation, t, telescope = TEST_LOGIN_ORG_SUBDOMAIN, None, None, None
    astronomer = (None, None)

    with patch.object(ArcsecondAPI, 'read', return_value=(org_details, None)) as mock_method_read_org, \
            patch.object(ArcsecondAPI, 'list', return_value=([], None)) as mock_method_list_org_telescopes:
        # Perform
        with pytest.raises(InvalidWatchOptionsOortCloudError):
            username, api_key, org_subdomain, org_role, telescope_details = \
                parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        assert mock_method_read_org.call_count == 1
        assert mock_method_list_org_telescopes.call_count == 1


@use_test_database
def test_cli_folders_loggedin_astronomer_with_o_option_with_invalid_telescope():
    """Case of an astronomer logged in and uploading for an organisation account.
    A valid telescope must be provided."""

    # Prepare
    save_test_credentials()

    tel_uuid = str(uuid.uuid4())
    org_details = {'subdomain': TEST_LOGIN_ORG_SUBDOMAIN}

    o, organisation, t, telescope = TEST_LOGIN_ORG_SUBDOMAIN, None, tel_uuid, None
    astronomer = (None, None)

    with patch.object(ArcsecondAPI, 'organisations',
                      return_value=ArcsecondAPI(debug=True, test=True)) as mock_method_api_org, \
            patch.object(ArcsecondAPI, 'telescopes',
                         return_value=ArcsecondAPI(debug=True, test=True)) as mock_method_api_tel, \
            patch.object(ArcsecondAPI, 'read') as mock_method_read:
        mock_method_read.side_effect = [(org_details, None), (None, ArcsecondError())]

        # Perform
        with pytest.raises(InvalidOrganisationTelescopeOortCloudError):
            username, api_key, org_subdomain, org_role, telescope_details = \
                parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        assert mock_method_api_org.call_count == 1
        assert mock_method_api_org.call_args_list[0].kwargs == {'debug': True, 'test': True}

        # Important check that telescopes list is fetched using the organisation keyword, that
        # will actually provide the list of telescopes for that organisation only.
        assert mock_method_api_tel.call_count == 1
        assert mock_method_api_tel.call_args_list[0].kwargs == \
               {'debug': True, 'test': True, 'organisation': TEST_LOGIN_ORG_SUBDOMAIN}

        assert mock_method_read.call_count == 2
        assert mock_method_read.call_args_list[0].kwargs == {}
        assert mock_method_read.call_args_list[1].kwargs == {}


@use_test_database
def test_cli_folders_loggedin_astronomer_with_o_and_t_options():
    """Case of an astronomer logged in and uploading for an organisation account.
    A valid telescope is provided."""

    save_test_credentials()

    tel_uuid = str(uuid.uuid4())
    tel_details = {'uuid': tel_uuid, 'name': 'telescope name', 'coordinates': {}}
    org_details = {'subdomain': TEST_LOGIN_ORG_SUBDOMAIN}

    o, organisation, t, telescope = None, TEST_LOGIN_ORG_SUBDOMAIN, tel_uuid, None
    astronomer = (None, None)

    with patch.object(ArcsecondAPI, 'read') as mock_method_read:
        mock_method_read.side_effect = [(org_details, None), (tel_details, None)]

        # Perform
        username, api_key, org_subdomain, org_role, telescope_details = \
            parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        # Assert
        assert mock_method_read.call_count == 2
        assert username == TEST_LOGIN_USERNAME
        assert api_key == ''
        assert org_subdomain == TEST_LOGIN_ORG_SUBDOMAIN
        assert org_role == TEST_LOGIN_ORG_ROLE
        assert telescope_details == tel_details


@use_test_database
def test_cli_folders_custom_astronomer_with_o_and_t_options_and_valid_upload_key():
    """Case of an astronomer logged in and uploading for an organisation account.
    A valid telescope is provided."""

    save_test_credentials()

    tel_uuid = str(uuid.uuid4())
    o, organisation, t, telescope = None, TEST_LOGIN_ORG_SUBDOMAIN, tel_uuid, None
    astronomer = ('custom', '1-2-3-4-5-6-7-8-9')

    org_details = {'subdomain': TEST_LOGIN_ORG_SUBDOMAIN}
    tel_details = {'uuid': tel_uuid, 'name': 'telescope name', 'coordinates': {}}
    astronomer_details = {'username': astronomer[0]}
    upload_keys = [{'username': astronomer[0], 'key': astronomer[1]}]

    with patch.object(ArcsecondAPI, 'read') as mock_method_read, \
            patch.object(ArcsecondAPI, 'list', return_value=(upload_keys, None)) as mock_method_list:
        mock_method_read.side_effect = [(org_details, None), (tel_details, None), (astronomer_details, None)]

        # Perform
        username, api_key, org_subdomain, org_role, telescope_details = \
            parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        # Assert
        assert mock_method_list.call_count == 1
        assert mock_method_read.call_count == 3
        assert username == astronomer[0]
        assert api_key == astronomer[1]
        assert org_subdomain == TEST_LOGIN_ORG_SUBDOMAIN
        assert org_role == TEST_LOGIN_ORG_ROLE
        assert telescope_details == tel_details

        folders = ['f1', 'f2']

        save_upload_folders(folders,
                            username,
                            api_key,
                            org_subdomain,
                            org_role,
                            telescope_details,
                            True)

        for folder_section in get_config_upload_folder_sections():
            identity = Identity.from_folder_section(folder_section, True)
            assert identity.username == username
            assert identity.api_key == api_key
            assert identity.subdomain == org_subdomain
            assert identity.role == org_role
            assert identity.telescope == telescope_details
