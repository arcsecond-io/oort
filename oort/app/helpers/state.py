import datetime
import json
import os

from configparser import ConfigParser, DuplicateOptionError

from arcsecond import Arcsecond


class Context:
    def __init__(self, config):
        self.debug = config['debug']
        self.folder = config['folder']
        self.organisation = config['organisation']

        self.username = Arcsecond.username(debug=self.debug)
        self.is_authenticated = Arcsecond.is_logged_in(debug=self.debug)
        self.memberships = Arcsecond.memberships(debug=self.debug)

        self.role = None
        if self.organisation is None:
            self.can_upload = True
        else:
            self.role = self.memberships.get(self.organisation, None)
            self.can_upload = self.role in ['member', 'admin', 'superadmin']

        self.config_filepath = os.path.expanduser('.oort.ini')
        self.current_date = config.get('current_date', self._get_current_date())

        self.payload = Payload()

        self._autostart = True
        self._uploads = {}

    def _get_current_date(self):
        before_noon = datetime.datetime.now().hour < 12
        if before_noon:
            return (datetime.datetime.now() - datetime.timedelta(days=1)).date().isoformat()
        else:
            return datetime.datetime.now().date().isoformat()

    def to_dict(self):
        return {
            'folder': self.folder,
            'username': self.username,
            'organisation': self.organisation,
            'role': self.role,
            'isAuthenticated': self.is_authenticated,
            'canUpload': self.can_upload,
            'debug': self.debug,
            'current_date': self.current_date
        }

    def get_yield_string(self):
        json_data = json.dumps(self.payload._payload)
        return f"data:{json_data}\n\n"


class Payload:
    def __init__(self):
        self._payload = {}

    def update(self, **kwargs):
        for key, value in kwargs.items():
            self._payload[key] = value

    def append(self, **kwargs):
        for key, value in kwargs.items():
            if key not in self._payload.keys():
                self._payload[key] = []
            self._payload[key].append(value)

    def get(self, key):
        return self._payload[key]

    def group_update(self, group, **kwargs):
        if group not in self._payload.keys():
            self._payload[group] = {}
        for key, value in kwargs.items():
            self._payload[group][key] = value

    def group_append(self, group, **kwargs):
        if group not in self._payload.keys():
            self._payload[group] = {}
        for key, value in kwargs.items():
            if key not in self._payload[group].keys():
                self._payload[group][key] = []
            if value not in self._payload[group][key]:
                self._payload[group][key].append(value)

    def group_get(self, group, key):
        if not group in self._payload.keys():
            return None
        if not key in self._payload[group]:
            return None
        return self._payload[group][key]


class State:
    def __init__(self, config):
        self.context = Context(config)

    @property
    def _section(self):
        raw_section = 'debug' if self.context.debug else 'main'
        return 'organisation:' + self.context.organisation + ':' + raw_section if self.context.organisation else raw_section

    def _get_config(self):
        _config = ConfigParser()
        try:
            _config.read(self.context.config_filepath)
        except DuplicateOptionError:
            os.remove(self.context.config_filepath)
            _config.read(self.context.config_filepath)
        return _config

    def _save_config(self, config):
        with open(self.context.config_filepath, 'w') as f:
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

    def get_yield_string(self):
        return self.context.get_yield_string()
