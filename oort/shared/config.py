import os
import tempfile
from configparser import ConfigParser, NoOptionError
from logging import DEBUG, FileHandler, Formatter, INFO, Logger, StreamHandler, getLogger
from pathlib import Path
from typing import Dict, List, Optional

from oort.shared.constants import OORT_SUPERVISOR_SOCK_FILENAME


def _get_directory_path() -> Path:
    path = Path('~/.oort').expanduser().resolve()
    if os.path.exists(str(path)) is False:
        os.mkdir(str(path))
    # path.mkdir(mode=0o755, exist_ok=True)
    return path


def get_oort_config_file_path() -> Path:
    return _get_directory_path() / 'config.ini'


def get_oort_config_socket_file_path() -> Path:
    return Path(tempfile.gettempdir()) / OORT_SUPERVISOR_SOCK_FILENAME


def get_oort_supervisord_log_file_path() -> Path:
    return _get_directory_path() / 'supervisord.log'


def get_oort_supervisord_pid_file_path() -> Path:
    return _get_directory_path() / 'supervisord.pid'


def get_oort_log_file_path() -> Path:
    return _get_directory_path() / 'oort.log'


def get_oort_db_file_path() -> Path:
    suffix = '-tests' if os.environ.get('OORT_TESTS') == '1' else ''
    return _get_directory_path() / f'uploads{suffix}.db'


def get_oort_supervisor_conf_file_path() -> Path:
    suffix = '-tests' if os.environ.get('OORT_TESTS') == '1' else ''
    return _get_directory_path() / f'supervisord{suffix}.conf'


def get_oort_logger(process_name, debug=False) -> Logger:
    suffix = '-tests' if os.environ.get('OORT_TESTS') == '1' else ''
    logger = getLogger('oort-cloud' + suffix)
    logger.setLevel(DEBUG if debug else INFO)

    if len(logger.handlers) == 0:
        formatter = Formatter('%(asctime)s - %(name)s[' + process_name + '] - %(levelname)s - %(message)s')

        if os.environ.get('OORT_TESTS') != '1':
            file_handler = FileHandler(str(get_oort_log_file_path()))
            file_handler.setLevel(DEBUG if debug else INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        console_handler = StreamHandler()
        console_handler.setLevel(DEBUG if debug else INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def write_oort_config_value(section: str, key: str, value) -> None:
    conf_file_path = get_oort_config_file_path()
    config = ConfigParser()
    if conf_file_path.exists():
        config.read(str(conf_file_path))
    if section not in config.sections():
        config.add_section(section)
    config.set(section, key, value)
    with conf_file_path.open('w') as f:
        config.write(f)


def write_oort_config_section_values(section: str, **kwargs):
    for k, v in kwargs.items():
        write_oort_config_value(section, k, v)


def get_oort_config_value(section: str, key: str) -> Optional[str]:
    conf_file_path = get_oort_config_file_path()
    config = ConfigParser()
    if conf_file_path.exists():
        config.read(str(conf_file_path))
    else:
        return None
    if section not in config.sections():
        return None
    try:
        return config.get(section, key)
    except NoOptionError:
        return None


def get_oort_config_upload_folder_sections() -> List[Dict]:
    conf_file_path = get_oort_config_file_path()
    if not conf_file_path.exists():
        return []

    config = ConfigParser()
    config.read(str(conf_file_path))

    use_tests = bool(os.environ.get('OORT_TESTS') == '1')
    sections = [
        section for section in config.sections() if
        section.startswith('watch-folder-') and section.endswith('-tests') == use_tests
    ]

    return [dict(config[section], **{'section': section}) for section in sections]


def update_oort_config_upload_folder_sections_key(upload_key) -> None:
    conf_file_path = get_oort_config_file_path()
    if not conf_file_path.exists():
        return None

    config = ConfigParser()
    config.read(str(conf_file_path))

    use_tests = os.environ.get('OORT_TESTS') == '1'
    for section in config.sections():
        if not section.startswith('watch-folder-'):
            continue
        if section.endswith('-tests') != use_tests:
            continue
        config.remove_option(section, 'upload_key')
        config.set(section, 'upload_key', upload_key)

    with conf_file_path.open('w') as f:
        config.write(f)


def get_oort_config_folder_section(section_name) -> Optional[Dict]:
    conf_file_path = get_oort_config_file_path()
    if not conf_file_path.exists():
        return None

    config = ConfigParser()
    config.read(str(conf_file_path))
    if config.has_section(section_name):
        return dict(config[section_name], **{'section': section_name})

    return None
