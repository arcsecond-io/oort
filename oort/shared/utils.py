import os
from configparser import ConfigParser

from .constants import OORT_FILENAME


def find_first_in_list(objects, **kwargs):
    return next((obj for obj in objects if
                 len(set(obj.keys()).intersection(kwargs.keys())) > 0 and
                 all([obj[k] == v for k, v in kwargs.items() if k in obj.keys()])),
                None)


class SafeDict(dict):
    def __init__(self, *args):
        dict.__init__(self, args)

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            return None

    def append(self, key, *items):
        if key not in self.keys():
            self[key] = []
        for item in items:
            if item not in self[key]:
                self[key].append(item)


def get_oort_config(path):
    _config = None
    oort_filepath = os.path.join(path, OORT_FILENAME)
    if os.path.exists(oort_filepath) and os.path.isfile(oort_filepath):
        # Below will fail if the info is missing / wrong.
        _config = ConfigParser()
        with open(oort_filepath, 'r') as f:
            _config.read(oort_filepath)
    return _config


def look_for_telescope_uuid(path):
    config = get_oort_config(path)
    if config and 'telescope' in config:
        return config['telescope']['uuid']
    return None
