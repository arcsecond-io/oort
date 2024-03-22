from oort.common.config import get_oort_config_upload_folder_sections
from oort.common.identity import Identity

from tests.utils import (TEST_LOGIN_ORG_ROLE,
                         TEST_LOGIN_ORG_SUBDOMAIN,
                         TEST_LOGIN_UPLOAD_KEY,
                         TEST_LOGIN_USERNAME,
                         clear_arcsecond_test_credentials,
                         clear_oort_test_folders)


def test_cli_folders_saving_and_prepare():
    clear_oort_test_folders()
    clear_arcsecond_test_credentials()

    identity = Identity(TEST_LOGIN_USERNAME,
                        TEST_LOGIN_UPLOAD_KEY,
                        TEST_LOGIN_ORG_SUBDOMAIN,
                        TEST_LOGIN_ORG_ROLE,
                        zip=True,
                        api='test')
    sections = get_oort_config_upload_folder_sections()
    assert len(sections) == 1

    prepared_folder_path, prepared_folder_identity = ['.', ], identity
    rebuilt_identity = Identity.from_folder_section(sections[0])

    assert prepared_folder_identity.username == rebuilt_identity.username
    assert prepared_folder_identity.upload_key == rebuilt_identity.upload_key
    assert prepared_folder_identity.subdomain == rebuilt_identity.subdomain
    assert prepared_folder_identity.role == rebuilt_identity.role
    assert prepared_folder_identity.telescope_uuid == rebuilt_identity.telescope_uuid
    assert prepared_folder_identity.zip == rebuilt_identity.zip
    assert prepared_folder_identity.api == rebuilt_identity.api
