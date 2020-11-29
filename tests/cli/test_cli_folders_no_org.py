import uuid
from unittest.mock import patch

import pytest
from arcsecond import ArcsecondAPI, ArcsecondError

from oort.cli.folders import parse_upload_watch_options
from oort.server.errors import InvalidOrganisationTelescopeOortCloudError
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
    save_test_credentials()

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
    save_test_credentials()

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
    save_test_credentials()

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
