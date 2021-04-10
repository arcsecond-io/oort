import uuid
from unittest.mock import patch

import pytest
from arcsecond import ArcsecondAPI, ArcsecondError

from oort.cli.folders import parse_upload_watch_options, save_upload_folders
from oort.server.errors import InvalidOrganisationTelescopeOortCloudError, InvalidWatchOptionsOortCloudError
from oort.shared.config import get_config_upload_folder_sections
from oort.shared.identity import Identity
from tests.utils import (
    TEST_LOGIN_API_KEY,
    TEST_LOGIN_ORG_ROLE,
    TEST_LOGIN_ORG_SUBDOMAIN,
    TEST_LOGIN_USERNAME,
    save_test_credentials,
    use_test_database
)

TEL_UUID = str(uuid.uuid4())
TEL_DETAILS = {'uuid': TEL_UUID, 'name': 'telescope name', 'coordinates': {}}
ORG_DETAILS = {'subdomain': TEST_LOGIN_ORG_SUBDOMAIN}
ORG_MEMBERSHIPS = {TEST_LOGIN_ORG_SUBDOMAIN: TEST_LOGIN_ORG_ROLE}
CUSTOM_ASTRONOMER = ('custom', '1-2-3-4-5-6-7-8-9')
CUSTOM_ASTRONOMER_DETAILS = {'username': CUSTOM_ASTRONOMER[0], 'key': CUSTOM_ASTRONOMER[1]}
UPLOAD_KEYS = [{'username': CUSTOM_ASTRONOMER[0], 'key': CUSTOM_ASTRONOMER[1]}]


@use_test_database
def test_cli_folders_with_options_org_as_o_but_no_telescope():
    save_test_credentials()

    with patch.object(ArcsecondAPI, 'read', return_value=(ORG_DETAILS, None)) as mock_read_org, \
            patch.object(ArcsecondAPI, 'list', return_value=([TEL_DETAILS, ], None)) as mock_list_org_telescopes:
        with pytest.raises(InvalidWatchOptionsOortCloudError):
            o, organisation, t, telescope, astronomer = TEST_LOGIN_ORG_SUBDOMAIN, None, None, None, (None, None)
            username, api_key, org_subdomain, org_role, tel_details = \
                parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        assert mock_read_org.call_count == 1
        assert mock_list_org_telescopes.call_count == 1


@use_test_database
def test_cli_folders_with_options_org_as_o_but_invalid_telescope():
    save_test_credentials()

    api = ArcsecondAPI(debug=True, test=True)
    with patch.object(ArcsecondAPI, 'read') as mock_read:
        mock_read.side_effect = [(ORG_DETAILS, None), (None, ArcsecondError())]

        with pytest.raises(InvalidOrganisationTelescopeOortCloudError):
            o, organisation, t, telescope, astronomer = TEST_LOGIN_ORG_SUBDOMAIN, None, 'dummy', None, (None, None)
            username, api_key, org_subdomain, org_role, tel_details = \
                parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        assert mock_read.call_count == 2


@use_test_database
def test_cli_folders_with_options_org_as_o_and_t():
    save_test_credentials()

    api = ArcsecondAPI(debug=True, test=True)
    with patch.object(ArcsecondAPI, 'read') as mock_read:
        mock_read.side_effect = [(ORG_DETAILS, None), (TEL_DETAILS, None)]

        o, organisation, t, telescope, astronomer = TEST_LOGIN_ORG_SUBDOMAIN, None, TEL_UUID, None, (None, None)
        username, api_key, org_subdomain, org_role, tel_details = \
            parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        # Assert
        assert mock_read.call_count == 2
        assert username == TEST_LOGIN_USERNAME
        assert api_key == TEST_LOGIN_API_KEY
        assert org_subdomain == TEST_LOGIN_ORG_SUBDOMAIN
        assert org_role == TEST_LOGIN_ORG_ROLE
        assert TEL_DETAILS == tel_details


@use_test_database
def test_cli_folders_custom_astronomer_with_o_and_t_options_and_valid_upload_key():
    save_test_credentials()

    with patch.object(ArcsecondAPI, 'read') as mock_read, \
            patch.object(ArcsecondAPI, 'list', return_value=(UPLOAD_KEYS, None)) as mock_list:
        mock_read.side_effect = [(ORG_DETAILS, None), (TEL_DETAILS, None), (CUSTOM_ASTRONOMER_DETAILS, None)]

        o, organisation, t, telescope, astronomer = TEST_LOGIN_ORG_SUBDOMAIN, None, TEL_UUID, None, CUSTOM_ASTRONOMER
        username, api_key, org_subdomain, org_role, tel_details = \
            parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        # Assert
        assert mock_list.call_count == 1
        assert mock_read.call_count == 3
        assert username == astronomer[0]
        assert api_key == astronomer[1]
        assert org_subdomain == TEST_LOGIN_ORG_SUBDOMAIN
        assert org_role == TEST_LOGIN_ORG_ROLE
        assert TEL_DETAILS == tel_details

        folders = ['f1', 'f2']

        save_upload_folders(folders,
                            username,
                            api_key,
                            org_subdomain,
                            org_role,
                            TEL_DETAILS,
                            True)

        for folder_section in get_config_upload_folder_sections():
            identity = Identity.from_folder_section(folder_section)
            assert identity.username == username
            assert identity.api_key == api_key
            assert identity.subdomain == org_subdomain
            assert identity.role == org_role
            assert identity.telescope == TEL_UUID
            assert identity.debug is True
