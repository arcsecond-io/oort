import datetime
import json
import os
from configparser import ConfigParser

from arcsecond import Arcsecond


class Context:
    def __init__(self, config):
        self.debug = config['debug']
        self.folder = config['folder']
        self.organisation = config['organisation']
        self.telescopeUUID = config['telescope']

        self.username = Arcsecond.username(debug=self.debug)
        self.is_authenticated = Arcsecond.is_logged_in(debug=self.debug)
        self.memberships = Arcsecond.memberships(debug=self.debug)

        self.role = None
        if self.organisation is not None:
            self.role = self.memberships.get(self.organisation, None)

        self.can_upload = self.organisation is None or self.role in ['member', 'admin', 'superadmin']

    def to_dict(self):
        return {'folder': self.folder,
                'username': self.username,
                'organisation': self.organisation,
                'role': self.role,
                'telescopeUUID': self.telescopeUUID,
                'isAuthenticated': self.is_authenticated,
                'canUpload': self.can_upload,
                'debug': self.debug}


class LocalState:
    def __init__(self, config):
        self.context = Context(config)
        self._config_filepath = os.path.expanduser('.oort.ini')
        self.payload = {}

    @property
    def current_date(self):
        before_noon = datetime.datetime.now().hour < 12
        if before_noon:
            return (datetime.datetime.now() - datetime.timedelta(days=1)).date().isoformat()
        else:
            return datetime.datetime.now().date().isoformat()

    def _create_remote_resource(self, api, name, **kwargs):
        response_resource, error = api.create(kwargs)
        if error:
            if self.context.debug: print(str(error))
            msg = f'Failed to create {name} for date {self.current_date}. Retry is automatic.'
            self.update_payload('warning', msg, 'messages')
        else:
            return response_resource

    def _find_or_create_remote_resource(self, name, api, **kwargs):
        new_resource = None
        response_list, error = api.list(**kwargs)
        if error:
            if self.context.debug: print(str(error))
            self.update_payload('warning', str(error), 'messages')
        elif len(response_list) == 0:
            new_resource = self._create_remote_resource(api, **kwargs)
        elif len(response_list) == 1:
            new_resource = response_list[0]
        else:
            msg = f'Multiple {name} found for date {self.current_date}? Choosing first.'
            if self.context.debug: print(msg)
            self.update_payload('warning', msg, 'messages')
        return new_resource

    def _check_existing_remote_resource(self, name, api, uuid):
        response_detail, error = api.read(uuid)
        if error:
            if self.context.debug: print(str(error))
            self.update_payload('warning', str(error), 'messages')
        elif response_detail:
            self.update_payload('warning', '', 'messages')
        else:
            msg = f"Unknown {name} with UUID {uuid}"
            if self.context.debug: print(msg)
            self.update_payload('warning', msg, 'messages')

    @property
    def _section(self):
        raw_section = 'debug' if self.context.debug else 'main'
        return 'organisation:' + self.context.organisation + ':' + raw_section if self.context.organisation else raw_section

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

    def update_payload(self, key, value, group=None):
        if group:
            if group not in self.payload.keys():
                self.payload[group] = {}
            self.payload[group][key] = value
        else:
            self.payload[key] = value

    def get_yield_string(self):
        json_data = json.dumps(self.payload)
        return f"data:{json_data}\n\n"
