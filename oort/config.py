import logging
import os


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


def get_logger():
    logger = logging.getLogger('oort-cloud')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(get_log_file_path())
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger
