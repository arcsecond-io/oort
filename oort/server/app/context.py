import datetime
import json

from arcsecond import ArcsecondAPI

from oort.shared.config import get_config_upload_folder_sections
from oort.shared.models import Upload


class Context:
    def __init__(self, config):
        self.debug = config['debug']
        self.start_time = datetime.datetime.utcnow()
        self.login_error = config.get('login_error')
        self.username = ArcsecondAPI.username(debug=self.debug)
        self.is_authenticated = ArcsecondAPI.is_logged_in(debug=self.debug)
        raw_memberships = ArcsecondAPI.memberships(debug=self.debug)
        self.memberships = {m: raw_memberships[m] for m in raw_memberships}

    def to_dict(self):
        return {
            'username': self.username,
            'isAuthenticated': self.is_authenticated,
            'memberships': self.memberships,
            'loginError': self.login_error,
            'debug': self.debug,
            'startTime': self.start_time.isoformat(),
            'folders': get_config_upload_folder_sections()
        }

    def get_yield_string(self):
        data = {
            'state': self.to_dict(),
            'pending': [u for u in Upload.select().where(Upload.status == 'pending').dicts()],
            'current': [u for u in Upload.select().where(Upload.status == 'current').dicts()],
            'finished': [u for u in Upload.select().where(Upload.status == 'finished').dicts()]
        }
        json_data = json.dumps(data)
        return f"data:{json_data}\n\n"
