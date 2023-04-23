import uuid
from unittest.mock import patch

from arcsecond import ArcsecondAPI
from click.testing import CliRunner

from oort.cli.cli import watch, folders
from oort.cli.folders import save_upload_folders
from oort.shared.config import get_oort_config_upload_folder_sections
from oort.shared.identity import Identity
from oort.shared.models import Organisation
from tests.utils import (TEST_LOGIN_ORG_ROLE,
                         TEST_LOGIN_ORG_SUBDOMAIN,
                         TEST_LOGIN_UPLOAD_KEY,
                         TEST_LOGIN_USERNAME,
                         clear_arcsecond_test_credentials,
                         clear_oort_test_folders,
                         use_test_database,
                         save_arcsecond_test_credentials)


@use_test_database
def test_cli_folders_saving_and_prepare():
    clear_oort_test_folders()
    clear_arcsecond_test_credentials()

    identity = Identity(TEST_LOGIN_USERNAME,
                        TEST_LOGIN_UPLOAD_KEY,
                        TEST_LOGIN_ORG_SUBDOMAIN,
                        TEST_LOGIN_ORG_ROLE,
                        zip=True,
                        api='test')
    prepared_folders = save_upload_folders(['.', ], identity)

    sections = get_oort_config_upload_folder_sections()
    assert len(sections) == 1

    prepared_folder_path, prepared_folder_identity = prepared_folders[0]
    rebuilt_identity = Identity.from_folder_section(sections[0])

    assert prepared_folder_identity.username == rebuilt_identity.username
    assert prepared_folder_identity.upload_key == rebuilt_identity.upload_key
    assert prepared_folder_identity.subdomain == rebuilt_identity.subdomain
    assert prepared_folder_identity.role == rebuilt_identity.role
    assert prepared_folder_identity.telescope_uuid == rebuilt_identity.telescope_uuid
    assert prepared_folder_identity.zip == rebuilt_identity.zip
    assert prepared_folder_identity.api == rebuilt_identity.api


@use_test_database
def test_cli_folders_no_folder():
    clear_oort_test_folders()
    clear_arcsecond_test_credentials()
    save_arcsecond_test_credentials()

    runner = CliRunner()
    result = runner.invoke(folders)
    assert 'No folder watched. Use `oort watch`' in result.output


@use_test_database
def test_cli_watch_one_valid_folder_no_org():
    clear_oort_test_folders()
    clear_arcsecond_test_credentials()
    save_arcsecond_test_credentials()

    runner = CliRunner()
    with patch('builtins.input', return_value='\n'):
        runner.invoke(watch, ['.', '--api', 'test'])
    result = runner.invoke(folders)
    assert 'Folder ID' in result.output
    assert 'username     = @robot1' in result.output
    assert 'upload_key   = ' in result.output
    assert 'telescope    = (no telescope)' in result.output
    assert 'organisation = (no organisation)' in result.output
    assert 'path         = ' in result.output
    assert 'zip          = False' in result.output


@use_test_database
def test_cli_unwatch_one_valid_folder_with_org():
    Organisation.create(subdomain=TEST_LOGIN_ORG_SUBDOMAIN)
    runner = CliRunner()
    telescope_uuid = str(uuid.uuid4())
    telescope_details = {'uuid': telescope_uuid, 'name': 'telescope name', 'coordinates': {}}

    with patch.object(ArcsecondAPI, 'read', return_value=(telescope_details, None)), \
            patch('builtins.input', return_value='\n'):
        runner.invoke(watch, ['.', '-o', TEST_LOGIN_ORG_SUBDOMAIN, '-t', telescope_uuid, '--api', 'test'])

        result = runner.invoke(folders)
        assert 'Folder ID' in result.output
        assert 'username     = @robot1' in result.output
        assert 'upload_key   = ' in result.output
        assert 'telescope    = ' + telescope_uuid in result.output
        assert 'organisation = ' + TEST_LOGIN_ORG_SUBDOMAIN + ' (role: admin)' in result.output
        assert 'path         = ' in result.output
        assert 'zip          = False' in result.output
