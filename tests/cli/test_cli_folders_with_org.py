from unittest.mock import patch

import pytest
from arcsecond import ArcsecondAPI, ArcsecondError

from oort.cli.folders import parse_upload_watch_options, save_upload_folders
from oort.server.errors import InvalidOrganisationTelescopeOortCloudError, InvalidWatchOptionsOortCloudError
from oort.shared.config import get_config_upload_folder_sections
from oort.shared.identity import Identity
from tests.utils import (CUSTOM_ASTRONOMER,
                         CUSTOM_ASTRONOMER_DETAILS,
                         ORG_DETAILS,
                         TEL_DETAILS,
                         TEL_UUID,
                         TEST_LOGIN_ORG_ROLE,
                         TEST_LOGIN_ORG_SUBDOMAIN,
                         TEST_LOGIN_UPLOAD_KEY,
                         TEST_LOGIN_USERNAME,
                         UPLOAD_KEYS,
                         save_test_credentials,
                         use_test_database)


@use_test_database
def test_cli_folders_with_options_org_but_no_telescope():
    save_test_credentials()

    with patch.object(ArcsecondAPI, 'read', return_value=(ORG_DETAILS, None)) as mock_read_org, \
            patch.object(ArcsecondAPI, 'list', return_value=([TEL_DETAILS, ], None)) as mock_list_org_telescopes:
        with pytest.raises(InvalidWatchOptionsOortCloudError):
            organisation, telescope, astronomer = TEST_LOGIN_ORG_SUBDOMAIN, None, (None, None)
            username, upload_key, org_subdomain, org_role, tel_details = \
                parse_upload_watch_options(organisation, telescope, astronomer, True)

        assert mock_read_org.call_count == 1
        assert mock_list_org_telescopes.call_count == 1


@use_test_database
def test_cli_folders_with_options_org_but_invalid_telescope():
    save_test_credentials()

    with patch.object(ArcsecondAPI, 'read') as mock_read:
        mock_read.side_effect = [(ORG_DETAILS, None), (None, ArcsecondError())]

        with pytest.raises(InvalidOrganisationTelescopeOortCloudError):
            organisation, telescope, astronomer = TEST_LOGIN_ORG_SUBDOMAIN, 'dummy', (None, None)
            username, upload_key, org_subdomain, org_role, tel_details = \
                parse_upload_watch_options(organisation, telescope, astronomer, True)

        assert mock_read.call_count == 2


@use_test_database
def test_cli_folders_with_options_org_and_telescope():
    save_test_credentials()

    with patch.object(ArcsecondAPI, 'read') as mock_read:
        mock_read.side_effect = [(ORG_DETAILS, None), (TEL_DETAILS, None)]

        organisation, telescope, astronomer = TEST_LOGIN_ORG_SUBDOMAIN, TEL_UUID, (None, None)
        username, upload_key, org_subdomain, org_role, tel_details = \
            parse_upload_watch_options(organisation, telescope, astronomer, True)

        # Assert
        assert mock_read.call_count == 2
        assert username == TEST_LOGIN_USERNAME
        assert upload_key == TEST_LOGIN_UPLOAD_KEY
        assert org_subdomain == TEST_LOGIN_ORG_SUBDOMAIN
        assert org_role == TEST_LOGIN_ORG_ROLE
        assert TEL_DETAILS == tel_details


@use_test_database
def test_cli_folders_custom_astronomer_with_o_and_t_options_and_valid_upload_key():
    save_test_credentials()

    with patch.object(ArcsecondAPI, 'read') as mock_read, \
            patch.object(ArcsecondAPI, 'list', return_value=(UPLOAD_KEYS, None)) as mock_list:
        mock_read.side_effect = [(ORG_DETAILS, None), (TEL_DETAILS, None), (CUSTOM_ASTRONOMER_DETAILS, None)]

        organisation, telescope, astronomer = TEST_LOGIN_ORG_SUBDOMAIN, TEL_UUID, CUSTOM_ASTRONOMER
        username, upload_key, org_subdomain, org_role, tel_details = \
            parse_upload_watch_options(organisation, telescope, astronomer, True, False)

        # Assert
        assert mock_list.call_count == 1
        assert mock_read.call_count == 3
        assert username == astronomer[0]
        assert upload_key == astronomer[1]
        assert org_subdomain == TEST_LOGIN_ORG_SUBDOMAIN
        assert org_role == TEST_LOGIN_ORG_ROLE
        assert TEL_DETAILS == tel_details

        folders = ['f1', 'f2']
        do_zip = True

        save_upload_folders(folders,
                            username,
                            upload_key,
                            org_subdomain,
                            org_role,
                            TEL_DETAILS,
                            do_zip,
                            True,
                            False)

        for folder_section in get_config_upload_folder_sections():
            identity = Identity.from_folder_section(folder_section)
            assert identity.username == username
            assert identity.upload_key == upload_key
            assert identity.subdomain == org_subdomain
            assert identity.role == org_role
            assert identity.telescope == TEL_UUID
            assert identity.debug is True
            assert identity.zip is do_zip
