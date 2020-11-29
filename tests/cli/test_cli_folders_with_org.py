import uuid
from unittest.mock import patch

import pytest
from arcsecond import ArcsecondAPI

from oort.cli.folders import parse_upload_watch_options
from oort.server.errors import InvalidWatchOptionsOortCloudError
from tests.utils import (
    TEST_LOGIN_ORG_ROLE,
    TEST_LOGIN_ORG_SUBDOMAIN,
    TEST_LOGIN_USERNAME,
    save_test_credentials,
    use_test_database
)


@use_test_database
def test_cli_folders_loggedin_astronomer_with_o_option_no_telescope():
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
def test_cli_folders_loggedin_astronomer_with_o_and_t_options():
    # Prepare
    save_test_credentials()

    tel_uuid = str(uuid.uuid4())
    tel_details = {'uuid': tel_uuid, 'name': 'telescope name', 'coordinates': {}}

    o, organisation, t, telescope = None, None, tel_uuid, None
    astronomer = (None, None)

    with patch.object(ArcsecondAPI, 'read', return_value=(tel_details, None)) as mock_method_read:
        # Perform
        username, api_key, org_subdomain, org_role, telescope_details = \
            parse_upload_watch_options(o, organisation, t, telescope, astronomer, True)

        # Assert
        assert username == TEST_LOGIN_USERNAME
        assert api_key == ''
        assert org_subdomain == TEST_LOGIN_ORG_SUBDOMAIN
        assert org_role == TEST_LOGIN_ORG_ROLE
        assert telescope_details == tel_details
