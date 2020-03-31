import json
import os
import datetime
from configparser import ConfigParser

from arcsecond import Arcsecond


class Context:
    def __init__(self, config):
        self.debug = config['debug']
        self.folder = config['folder']
        self.organisation = config['organisation']
        self.telescope = config['telescope']

        self.username = Arcsecond.username(debug=self.debug)
        self.isAuthenticated = Arcsecond.is_logged_in(debug=self.debug)
        self.memberships = Arcsecond.memberships(debug=self.debug)

        self.role = None
        if self.organisation is not None:
            self.role = self.memberships.get(self.organisation, None)

        self.canUpload = self.organisation is None or self.role in ['member', 'admin', 'superadmin']

    def to_dict(self):
        return {'folder': self.folder,
                'isAuthenticated': self.isAuthenticated,
                'username': self.username,
                'organisation': self.organisation,
                'role': self.role,
                'telescope': self.telescope,
                'canUpload': self.canUpload}


class LocalState:
    def __init__(self, config):
        self.context = Context(config)
        self._config_filepath = os.path.expanduser('.oort.ini')
        self.payload = {}

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


class AdminLocalState(LocalState):
    def __init__(self, config):
        super().__init__(config)
        self.update_payload('admin', self.context.to_dict())

        self.telescopes_api = Arcsecond.build_telescopes_api(debug=self.context.debug,
                                                             organisation=self.context.organisation)

        self.logs_api = Arcsecond.build_nightlogs_api(debug=self.context.debug,
                                                      organisation=self.context.organisation)

    def _check_remote_telescope(self, ):
        telescope, error = self.telescopes_api.read(self.context.telescope)
        if error:
            self.update_payload('message', str(error), 'admin')
        elif telescope:
            self.update_payload('message', '', 'admin')
            self.update_payload('telescope', telescope, 'admin')
            self.save(telescope=json.dumps(telescope))
        else:
            self.update_payload('message', f"Unknown telescope with UUID {self.context.telescope}", 'admin')

    def sync_telescope(self):
        self.update_payload('message', '', 'admin')
        local_telescope = json.loads(self.read('telescope') or '{}')

        if local_telescope and self.context.telescope:
            # Check if they are the same
            if local_telescope['uuid'] == self.context.telescope:
                self.update_payload('telescope', local_telescope, 'admin')
            else:
                # If not, telescope provided in CLI takes precedence.
                self._check_remote_telescope()

        elif local_telescope and not self.context.telescope:
            self.update_payload('telescope', local_telescope, 'admin')

        elif not local_telescope and self.context.telescope:
            self._check_remote_telescope()

        else:
            # Do nothing
            pass

    def sync_night_log(self):
        local_telescope = json.loads(self.read('telescope') or '{}')
        if not local_telescope:
            return

        before_noon = datetime.datetime.now().hour < 12
        if before_noon:
            date = (datetime.datetime.now() - datetime.timedelta(days=1)).date().isoformat()
        else:
            date = datetime.datetime.now().date().isoformat()

        self.update_payload('date', date, 'admin')
        local_nightlog = json.loads(self.read('night_log') or '{}')

        if local_nightlog:
            self.update_payload('night_log', local_nightlog, 'admin')
        else:
            logs, error = self.logs_api.list(date=date)

            if error:
                self.update_payload('message', str(error), 'admin')
            elif len(logs) == 0:
                result, error = self.logs_api.create({'date': date, 'telescope': local_telescope['uuid']})
                if error:
                    pass
                elif result:
                    self.save(night_log=json.dumps(result))
                    self.update_payload('night_log', result, 'admin')
            elif len(logs) == 1:
                self.save(night_log=json.dumps(logs[0]))
                self.update_payload('night_log', logs[0], 'admin')
            else:
                self.update_payload('message', f'Multiple logs found for date {date}', 'admin')
