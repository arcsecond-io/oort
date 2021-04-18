import logging
import os
import tempfile
from configparser import ConfigParser, NoOptionError
from typing import Dict, List, Optional

from oort.shared.constants import OORT_SUPERVISOR_SOCK_FILENAME


def get_directory_path():
    d = os.path.expanduser('~/.oort')
    if os.path.exists(d) is False:
        os.mkdir(d)
    return d


def get_oort_config_file_path():
    return os.path.join(get_directory_path(), 'config.ini')


def get_config_socket_file_path():
    return os.path.join(tempfile.gettempdir(), OORT_SUPERVISOR_SOCK_FILENAME)


def get_supervisord_log_file_path():
    return os.path.join(get_directory_path(), 'supervisord.log')


def get_supervisord_pid_file_path():
    return os.path.join(get_directory_path(), 'supervisord.pid')


def get_log_file_path():
    return os.path.join(get_directory_path(), 'oort.log')


def get_db_file_path():
    suffix = '-tests' if os.environ.get('OORT_TESTS') == '1' else ''
    return os.path.join(get_directory_path(), f'uploads{suffix}.db')


def get_supervisor_conf_file_path():
    return os.path.join(get_directory_path(), 'supervisord.conf')


def get_logger(debug=False):
    suffix = '-tests' if os.environ.get('OORT_TESTS') == '1' else ''
    logger = logging.getLogger('oort-cloud' + suffix)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    if len(logger.handlers) == 0:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        file_handler = logging.FileHandler(get_log_file_path())
        file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def write_config_value(section: str, key: str, value):
    conf_file_path = get_oort_config_file_path()
    config = ConfigParser()
    if os.path.exists(conf_file_path):
        config.read(conf_file_path)
    if section not in config.sections():
        config.add_section(section)
    config.set(section, key, value)
    with open(conf_file_path, 'w') as f:
        config.write(f)


def write_config_section_values(section: str, **kwargs):
    for k, v in kwargs.items():
        write_config_value(section, k, v)


def get_config_value(section: str, key: str):
    conf_file_path = get_oort_config_file_path()
    config = ConfigParser()
    if os.path.exists(conf_file_path):
        config.read(conf_file_path)
    else:
        return None
    if section not in config.sections():
        return None
    try:
        return config.get(section, key)
    except NoOptionError:
        return None


def get_config_upload_folder_sections() -> List[Dict]:
    conf_file_path = get_oort_config_file_path()
    if not os.path.exists(conf_file_path):
        return []
    config = ConfigParser()
    config.read(conf_file_path)

    if os.environ.get('OORT_TESTS') == '1':
        sections = [
            section for section in config.sections() if
            section.startswith('watch-folder-') and section.endswith('-tests')
        ]
    else:
        sections = [
            section for section in config.sections() if
            section.startswith('watch-folder-') and not section.endswith('-tests')
        ]

    return [dict(config[section], **{'section': section}) for section in sections]


def get_config_folder_section(section_name) -> Optional[Dict]:
    conf_file_path = get_oort_config_file_path()
    if not os.path.exists(conf_file_path):
        return None
    config = ConfigParser()
    config.read(conf_file_path)
    if config.has_section(section_name):
        return dict(config[section_name], **{'section': section_name})
    return None
