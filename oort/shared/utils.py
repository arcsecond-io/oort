import datetime
import os
import random
import string
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


def look_for_telescope_uuid(path):
    oort_filepath = os.path.join(path, OORT_FILENAME)
    if os.path.exists(oort_filepath) and os.path.isfile(oort_filepath):
        # Below will fail if the info is missing / wrong.
        config = ConfigParser()
        with open(oort_filepath, 'r') as f:
            config.read(oort_filepath)
            if 'telescope' in config:
                return config['telescope']['uuid']
    return None


def get_current_date(self):
    before_noon = datetime.datetime.now().hour < 12
    if before_noon:
        return (datetime.datetime.now() - datetime.timedelta(days=1)).date().isoformat()
    else:
        return datetime.datetime.now().date().isoformat()


def get_random_string(n):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))
