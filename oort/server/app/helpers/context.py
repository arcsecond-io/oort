import datetime
import json

from arcsecond import Arcsecond

from .utils import SafeDict


class Context:
    def __init__(self, config):
        self.debug = config['debug']
        self.verbose = config['verbose']
        self.folder = config['folder']
        self.organisation = config['organisation']

        self.login_error = config.get('login_error')
        self.username = Arcsecond.username(debug=self.debug)
        self.is_authenticated = Arcsecond.is_logged_in(debug=self.debug)
        self.memberships = Arcsecond.memberships(debug=self.debug)

        self.role = None
        if self.organisation is None:
            self.can_upload = True
        else:
            self.role = self.memberships.get(self.organisation, None)
            self.can_upload = self.role in ['member', 'admin', 'superadmin']

        self.state = self.to_dict()
        self.messages = SafeDict()

        self.telescopes = []
        self.night_logs = SafeDict()

        self.uploads = []
        self.fileuploaders = {}
        self._autostart = True

    def _get_current_date(self):
        before_noon = datetime.datetime.now().hour < 12
        if before_noon:
            return (datetime.datetime.now() - datetime.timedelta(days=1)).date().isoformat()
        else:
            return datetime.datetime.now().date().isoformat()

    def refresh_uploads(self):
        self.uploads = [fw.to_dict() for fw in self.fileuploaders.values()]

    def to_dict(self):
        return {
            'folder': self.folder,
            'username': self.username,
            'organisation': self.organisation,
            'role': self.role,
            'isAuthenticated': self.is_authenticated,
            'loginError': self.login_error,
            'canUpload': self.can_upload,
            'debug': self.debug,
            'verbose': self.verbose
        }

    def get_count(self, state_name):
        return len([u for u in self.uploads if u['state'] == state_name])

    def get_yield_string(self):
        data = {
            'state': self.state,
            'messages': self.messages,
            'telescopes': list(self.telescopes),
            'night_logs': list(self.night_logs),
            'uploads': self.uploads
        }
        print(f"yield {self.get_count('pending')} {self.get_count('current')} {self.get_count('finished')}")
        json_data = json.dumps(data)
        return f"data:{json_data}\n\n"
