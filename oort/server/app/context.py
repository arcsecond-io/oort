import datetime
import json

from arcsecond import Arcsecond
from oort.shared.config import get_config_upload_folder_sections


class Context:
    def __init__(self, config):
        self.debug = config['debug']
        self.start_time = datetime.datetime.utcnow()
        self.login_error = config.get('login_error')
        self.username = Arcsecond.username(debug=self.debug)
        self.is_authenticated = Arcsecond.is_logged_in(debug=self.debug)

    def to_dict(self):
        return {
            'username': self.username,
            'isAuthenticated': self.is_authenticated,
            'loginError': self.login_error,
            'debug': self.debug,
            'startTime': self.start_time.isoformat(),
            'folders': get_config_upload_folder_sections()
        }

    def get_yield_string(self):
        data = {
            'state': self.to_dict()
        }
        json_data = json.dumps(data)
        return f"data:{json_data}\n\n"
