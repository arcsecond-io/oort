import datetime
import json
from json import JSONEncoder
from uuid import UUID

from arcsecond import ArcsecondAPI
from playhouse.shortcuts import model_to_dict

from oort.shared.config import get_config_upload_folder_sections
from oort.shared.models import (Dataset, STATUS_ERROR, STATUS_NEW, STATUS_OK, STATUS_PREPARING,
                                SUBSTATUS_ALREADY_SYNCED, SUBSTATUS_DONE, SUBSTATUS_READY, SUBSTATUS_SKIPPED,
                                SUBSTATUS_STARTING, SUBSTATUS_UPLOADING, Upload)


class BoostedJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return f'{o:%Y-%m-%d %H:%M:%S%z}'
        if isinstance(o, UUID):
            return str(o)
        return super().default(o)


class Context:
    def __init__(self, config):
        self.debug = config['debug']
        self.start_time = datetime.datetime.utcnow()
        self.login_error = config.get('login_error')
        self.username = ArcsecondAPI.username(debug=self.debug)
        self.is_authenticated = ArcsecondAPI.is_logged_in(debug=self.debug)
        self.memberships = ArcsecondAPI.memberships(debug=self.debug)

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
        pending_query = Upload.select().where((Upload.status == STATUS_NEW) | (Upload.status == STATUS_PREPARING))
        current_query = Upload.select().where(Upload.status == SUBSTATUS_UPLOADING)
        error_query = Upload.select().where(Upload.status == STATUS_ERROR)
        one_day_back = datetime.datetime.now() - datetime.timedelta(days=1)
        finished_query = Upload.select().where(Upload.status == SUBSTATUS_DONE).where(Upload.ended >= one_day_back)

        def _ff(u):
            # fill and flatten
            if u.get('dataset', None) is not None:
                ds = Dataset.get(Dataset.uuid == u['dataset']['uuid'])
                if ds.observation is not None:
                    u['observation'] = model_to_dict(ds.observation, recurse=False)
                if ds.calibration is not None:
                    u['calibration'] = model_to_dict(ds.calibration, recurse=False)
                obs_or_calib = ds.observation or ds.calibration
                u['night_log'] = model_to_dict(obs_or_calib.night_log, recurse=False)
            else:
                u['observation'] = {}
                u['calibration'] = {}
                u['night_log'] = {}
            if u.get('telescope') is None:
                u['telescope'] = {}
            return u

        data = {
            'state': self.to_dict(),
            'pending': [_ff(model_to_dict(u, max_depth=1)) for u in pending_query],
            'current': [_ff(model_to_dict(u, max_depth=1)) for u in current_query],
            'finished': [_ff(model_to_dict(u, max_depth=1)) for u in finished_query.order_by(-Upload.ended)],
            'errors': [_ff(model_to_dict(u, max_depth=1)) for u in error_query]
        }
        json_data = json.dumps(data, cls=BoostedJSONEncoder)
        # print(json_data)
        return f"data:{json_data}\n\n"
