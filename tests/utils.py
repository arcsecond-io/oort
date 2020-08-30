import inspect
import sys
from functools import wraps

import httpretty
import peewee
from arcsecond import cli
from arcsecond.api.constants import API_AUTH_PATH_LOGIN, ARCSECOND_API_URL_DEV
from click.testing import CliRunner

from oort.shared.models import BaseModel

TEST_LOGIN_USERNAME = 'robot1'
TEST_LOGIN_PASSWORD = 'robotpass'
TEST_API_KEY = '935e2b9e24c44581b4ef5f4c8e53213e'


def register_successful_personal_login():
    runner = CliRunner()
    httpretty.register_uri(
        httpretty.POST,
        ARCSECOND_API_URL_DEV + API_AUTH_PATH_LOGIN,
        status=200,
        body='{ "key": "935e2b9e24c44581b4ef5f4c8e53213e935e2b9e24c44581b4ef5f4c8e53213e" }'
    )
    httpretty.register_uri(
        httpretty.GET,
        ARCSECOND_API_URL_DEV + '/profiles/' + TEST_LOGIN_USERNAME + '/keys/',
        status=200,
        body='{ "api_key": "' + TEST_API_KEY + '" }'
    )
    result = runner.invoke(cli.login, ['-d'], input=TEST_LOGIN_USERNAME + '\n' + TEST_LOGIN_PASSWORD)
    assert result.exit_code == 0


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
