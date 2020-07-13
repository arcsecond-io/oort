import os


def get_directory_path():
    d = os.path.expanduser('~/.oort')
    if os.path.exists(d) is False:
        os.mkdir(d)
    return d


def get_config_file_path():
    return os.path.join(get_directory_path(), 'config.ini')


def get_db_file_path():
    return os.path.join(get_directory_path(), 'uploads.db')
