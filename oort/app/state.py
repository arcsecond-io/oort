import os
from configparser import ConfigParser


class State:
    def __init__(self, organisation, debug):
        self.organisation = organisation
        self.debug = debug
        raw_section = 'debug' if debug else 'main'
        self._section = 'organisation:' + organisation + ':' + raw_section if organisation else raw_section
        self._config_filepath = os.path.expanduser('.oort.ini')

    def _get_config(self):
        _config = ConfigParser()
        _config.read(self._config_filepath)
        return _config

    def _save_config(self, config):
        with open(self._config_filepath, 'w') as f:
            config.write(f)

    def read(self, key):
        config = self._get_config()
        if self._section not in config.keys():
            return None
        return config[self._section].get(key)

    def save(self, **kwargs):
        config = self._get_config()
        if self._section not in config.keys():
            config.add_section(self._section)
        for k, v in kwargs.items():
            config.set(self._section, k, v)
        self._save_config(config)
