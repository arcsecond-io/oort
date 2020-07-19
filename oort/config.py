import logging
import os

from configparser import ConfigParser


def get_directory_path():
    d = os.path.expanduser('~/.oort')
    if os.path.exists(d) is False:
        os.mkdir(d)
    return d


def get_config_file_path():
    return os.path.join(get_directory_path(), 'config.ini')


def get_log_file_path():
    return os.path.join(get_directory_path(), 'uploads.log')


def get_db_file_path():
    return os.path.join(get_directory_path(), 'uploads.db')


def get_supervisor_conf_file_path():
    return os.path.join(get_directory_path(), 'supervisord.conf')


def get_logger(debug=False):
    logger = logging.getLogger('oort-cloud')
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    fh = logging.FileHandler(get_log_file_path())
    fh.setLevel(logging.DEBUG if debug else logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    if debug is True:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)
    return logger


def write_config_value(section, key, value):
    conf_file_path = get_config_file_path()
    config = ConfigParser()
    if os.path.exists(conf_file_path):
        config.read(conf_file_path)
    if section not in config.sections():
        config.add_section(section)
    config.set(section, key, value)
    with open(conf_file_path, 'w') as f:
        config.write(f)


def get_config_value(section, key):
    conf_file_path = get_config_file_path()
    config = ConfigParser()
    if os.path.exists(conf_file_path):
        config.read(conf_file_path)
    else:
        return None
    if section not in config.sections():
        return None
    return config.get(section, key)
