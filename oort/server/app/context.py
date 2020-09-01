import datetime
import json
from json import JSONEncoder
from uuid import UUID

from arcsecond import ArcsecondAPI
from playhouse.shortcuts import model_to_dict

from oort.shared.config import get_config_upload_folder_sections
from oort.shared.models import (Dataset, Status, Upload)


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
        pending_query = Upload.select().where(
            (Upload.status == Status.NEW.value) |
            (Upload.status == Status.PREPARING.value)
        )
        current_query = Upload.select().where(Upload.status == Status.UPLOADING.value)
        error_query = Upload.select().where(Upload.status == Status.ERROR.value)

        one_day_back = datetime.datetime.now() - datetime.timedelta(days=7)
        finished_query = Upload.select().where(Upload.status == Status.OK.value).where(Upload.ended >= one_day_back)

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
                u['night_log'] = {}
            return u

        state = self.to_dict()
        state.update(hiddenCount=Upload.select()
                     .where(Upload.status == Status.OK.value)
                     .where(Upload.ended < one_day_back).count())

        data = {
            'state': state,
            'pending': [_ff(model_to_dict(u, max_depth=1)) for u in pending_query.order_by(Upload.created)],
            'current': [_ff(model_to_dict(u, max_depth=1)) for u in current_query],
            'finished': [_ff(model_to_dict(u, max_depth=1)) for u in finished_query.order_by(-Upload.ended)],
            'errors': [_ff(model_to_dict(u, max_depth=1)) for u in error_query]
        }
        json_data = json.dumps(data, cls=BoostedJSONEncoder)
        # print(json_data)
        return f"data:{json_data}\n\n"
