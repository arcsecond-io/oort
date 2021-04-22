import datetime
import json
from http.client import CannotSendRequest
from json import JSONEncoder
from uuid import UUID
from xmlrpc.client import ServerProxy

from arcsecond import ArcsecondAPI
from playhouse.shortcuts import model_to_dict

from oort.shared.config import get_config_folder_section, get_config_upload_folder_sections, get_config_value
from oort.shared.models import (Dataset, Status, Upload)


class BoostedJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return f'{o:%Y-%m-%d %H:%M:%S%z}'
        if isinstance(o, UUID):
            return str(o)
        return super().default(o)


class Context:
    """Context class used only once, and associated with the currently
    logged in user, not a potential custom astronomer."""

    def __init__(self, config):
        self.debug = bool(config.get('debug', 'False'))
        self.start_time = datetime.datetime.utcnow()
        self.login_error = config.get('login_error')
        self.username = ArcsecondAPI.username(debug=self.debug)
        self.is_authenticated = ArcsecondAPI.is_logged_in(debug=self.debug)
        self._memberships = ArcsecondAPI.memberships(debug=self.debug)
        self._uploader = ServerProxy('http://localhost:9001/RPC2')

    def _get_uploader_state(self):
        try:
            _info = self._uploader.supervisor.getProcessInfo('oort-uploader')
        except (ConnectionRefusedError, CannotSendRequest) as e:
            return str(e)[:30] + '...'
        else:
            return _info.get('statename')

    def updateUploader(self, action):
        _info = self._uploader.supervisor.getProcessInfo('oort-uploader')
        if action == 'stop' and _info.get('statename') == 'RUNNING':
            self._uploader.supervisor.stopProcess('oort-uploader')
        elif action == 'start' and _info.get('statename') == 'STOPPED':
            self._uploader.supervisor.startProcess('oort-uploader')

    def to_dict(self):
        return {
            'username': self.username,
            'isAuthenticated': self.is_authenticated,
            'loginError': self.login_error,
            'debug': self.debug,
            'startTime': self.start_time.isoformat(),
            'folders': get_config_upload_folder_sections(),
            'uploaderState': self._get_uploader_state()
        }

    def _get_queries_dicts(self, selected_path: str):
        pending_query = Upload.select() \
            .where(Upload.file_path.startswith(selected_path)) \
            .where(Upload.status == Status.NEW.value)

        current_query = Upload.select() \
            .where(Upload.file_path.startswith(selected_path)) \
            .where((Upload.status == Status.PREPARING.value) | (Upload.status == Status.UPLOADING.value))

        error_query = Upload.select() \
            .where(Upload.file_path.startswith(selected_path)) \
            .where(Upload.status == Status.ERROR.value)

        one_day_back = datetime.datetime.now() - datetime.timedelta(days=7)
        finished_query = Upload.select() \
            .where(Upload.file_path.startswith(selected_path)) \
            .where(Upload.status == Status.OK.value) \
            .where(Upload.ended >= one_day_back)

        hidden_query = Upload.select() \
            .where(Upload.file_path.startswith(selected_path)) \
            .where(Upload.status == Status.OK.value) \
            .where(Upload.ended < one_day_back)

        hidden_count = hidden_query.count()
        pending_count = pending_query.count()
        current_count = current_query.count()
        error_count = error_query.count()
        finished_count = finished_query.count()
        skipped_count = finished_query.where(Upload.substatus.startswith('skipped')).count()

        def _ff(u):
            # fill and flatten
            u['night_log'] = {}
            if u.get('dataset', None) is not None:
                ds = Dataset.get(Dataset.uuid == u['dataset']['uuid'])
                if ds.observation is not None:
                    u['observation'] = model_to_dict(ds.observation, recurse=False)
                if ds.calibration is not None:
                    u['calibration'] = model_to_dict(ds.calibration, recurse=False)
                obs_or_calib = ds.observation or ds.calibration
                if obs_or_calib:
                    u['night_log'] = model_to_dict(obs_or_calib.night_log, recurse=False)
            return u

        return {
            'counts': {
                'hidden': hidden_count,
                'pending': pending_count,
                'current': current_count,
                'error': error_count,
                'finished': finished_count,
                'skipped': skipped_count
            },
            'pending': [_ff(model_to_dict(u, max_depth=1)) for u in
                        pending_query.limit(1000).order_by(Upload.created).iterator()],
            'current': [_ff(model_to_dict(u, max_depth=1)) for u in
                        current_query.order_by(Upload.created).iterator()],
            'finished': [_ff(model_to_dict(u, max_depth=1)) for u in
                         finished_query.limit(1000).order_by(-Upload.ended).iterator()],
            'errors': [_ff(model_to_dict(u, max_depth=1)) for u in
                       error_query.limit(1000).order_by(Upload.created).iterator()]
        }

    def get_yield_string(self) -> str:
        data = {'state': self.to_dict()}

        selected_folder = get_config_value('server', 'selected_folder')
        selected_section = get_config_folder_section(selected_folder)
        if selected_section:
            data.update(**self._get_queries_dicts(selected_section.get('path')))
            subdomain = selected_section.get('subdomain')
            if subdomain:
                role = self._memberships.get(subdomain)
                if role:
                    data['state'].update(membership=(subdomain, role))

        json_data = json.dumps(data, cls=BoostedJSONEncoder)
        # print(json_data)
        return f"data:{json_data}\n\n"  ## having 2 line returns is key to distinguish response streams packets.
