import inspect
import sys
import uuid
from configparser import ConfigParser
from functools import wraps

import httpretty
import peewee
from arcsecond.api.constants import ARCSECOND_API_URL_DEV
from arcsecond.config import (config_file_clear_section,
                              config_file_save_organisation_membership,
                              config_file_save_upload_key)

from oort.shared.config import get_oort_config_file_path, get_oort_config_upload_folder_sections
from oort.shared.models import BaseModel

TEST_LOGIN_USERNAME = 'robot1'
TEST_LOGIN_PASSWORD = 'robotpass'

TEST_LOGIN_ORG_SUBDOMAIN = 'robotland'
TEST_LOGIN_ORG_ROLE = 'admin'
TEST_LOGIN_UPLOAD_KEY = '935e2b9e24c44581b4ef5f4c8e53213e'

TEST_CUSTOM_USERNAME = 'astronomer'
TEST_CUSTOM_UPLOAD_KEY = '5e2b9e4ef5f4c8e53224c4458113e93b'

TEL_UUID = str(uuid.uuid4())
TEL_DETAILS = {'uuid': TEL_UUID, 'name': 'telescope name', 'coordinates': {}}
ORG_DETAILS = {'subdomain': TEST_LOGIN_ORG_SUBDOMAIN}
ORG_MEMBERSHIPS = {TEST_LOGIN_ORG_SUBDOMAIN: TEST_LOGIN_ORG_ROLE}


# CUSTOM_ASTRONOMER = ('custom', '1-2-3-4-5-6-7-8-9')
# CUSTOM_ASTRONOMER_DETAILS = {'username': CUSTOM_ASTRONOMER[0], 'key': CUSTOM_ASTRONOMER[1]}
# UPLOAD_KEYS = [{'username': CUSTOM_ASTRONOMER[0], 'key': CUSTOM_ASTRONOMER[1]}]


def save_arcsecond_test_credentials(username=TEST_LOGIN_USERNAME, subdomain=TEST_LOGIN_ORG_SUBDOMAIN):
    clear_arcsecond_test_credentials()
    config_file_save_upload_key(TEST_LOGIN_UPLOAD_KEY, username, section='test')
    if subdomain == TEST_LOGIN_ORG_SUBDOMAIN:
        config_file_save_organisation_membership(subdomain, TEST_LOGIN_ORG_ROLE, section='test')


def clear_arcsecond_test_credentials():
    config_file_clear_section('test')


def clear_oort_test_folders():
    conf_file_path = get_oort_config_file_path()
    config = ConfigParser()
    config.read(str(conf_file_path))

    print(get_oort_config_upload_folder_sections())
    sections = [s for s in get_oort_config_upload_folder_sections() if s.get('section').endswith('-tests')]
    print(sections)
    for section in sections:
        if section.get('section') in config.sections():
            del config[section.get('section')]
            print(section)

    with conf_file_path.open('w') as f:
        config.write(f)


def mock_url_path(method, path, body='', query='', status=200):
    path = path + '/' if path[-1] != '/' else path
    httpretty.register_uri(method,
                           ARCSECOND_API_URL_DEV + path + query,
                           status=status,
                           body=body,
                           match_querystring=True)


def mock_http_get(path, body='{}', status=200):
    mock_url_path(httpretty.GET, path, body, status=status)


def mock_http_post(path, body='{}', status=200):
    mock_url_path(httpretty.POST, path, body, status=status)


MODELS = [m[1] for m in inspect.getmembers(sys.modules['oort.shared.models'], inspect.isclass) if
          issubclass(m[1], peewee.Model) and m[1] != peewee.Model and m[1] != BaseModel]


def use_test_database(fn):
    test_db = peewee.SqliteDatabase(':memory:')

    # To have an asyncio compatible version:
    # - decorate tests with @pytest.mark.asyncio
    # - add `async` before `def inner`
    # - add `await` before `fn()`

    @wraps(fn)
    def inner():
        with test_db.bind_ctx(MODELS):
            test_db.create_tables(MODELS)
            try:
                fn()
            finally:
                test_db.drop_tables(MODELS)

    return inner
