import json
import datetime

from arcsecond import Arcsecond

from .models.obstech import NightLog
from .state import LocalState


class AdminLocalState(LocalState):
    def __init__(self, config):
        super().__init__(config)
        self.update_payload('admin', self.context.to_dict())

        self.night_log = NightLog(self.context.folder, self.current_date)

        self.telescopes_api = Arcsecond.build_telescopes_api(debug=self.context.debug,
                                                             organisation=self.context.organisation)

        self.logs_api = Arcsecond.build_nightlogs_api(debug=self.context.debug,
                                                      organisation=self.context.organisation)

    @property
    def current_date(self):
        before_noon = datetime.datetime.now().hour < 12
        if before_noon:
            return (datetime.datetime.now() - datetime.timedelta(days=1)).date().isoformat()
        else:
            return datetime.datetime.now().date().isoformat()

    def _check_remote_telescope(self, tel_uuid):
        response_telescope, error = self.telescopes_api.read(tel_uuid)
        if error:
            if self.context.debug: print(str(error))
            self.update_payload('message', str(error), 'admin')
        elif response_telescope:
            self.update_payload('message', '', 'admin')
            return response_telescope
        else:
            self.update_payload('message', f"Unknown telescope with UUID {tel_uuid}", 'admin')
            self.save(telescopes='')

    def sync_telescopes(self):
        valid_telescopes = []
        for telescope in self.night_log.telescopes:
            valid_telescope = self._check_remote_telescope(telescope.uuid)
            if valid_telescope:
                valid_telescopes.append(valid_telescope)
        self.update_payload('telescopes', valid_telescopes, 'admin')
        self.save(telescopes=json.dumps(valid_telescopes))

    def sync_single_telescope(self):
        self.update_payload('message', '', 'admin')
        local_telescope = json.loads(self.read('telescope') or '{}')
        valid_telescope = None

        if local_telescope and self.context.telescopeUUID:
            # Check if they are the same
            if local_telescope['uuid'] == self.context.telescopeUUID:
                self.update_payload('telescopes', [local_telescope], 'admin')
            else:
                # If not, telescope provided in CLI takes precedence, even if it fails...
                valid_telescope = self._check_remote_telescope(local_telescope['uuid'])

        elif local_telescope and not self.context.telescopeUUID:
            self.update_payload('telescopes', [local_telescope], 'admin')

        elif not local_telescope and self.context.telescopeUUID:
            valid_telescope = self._check_remote_telescope(self.context.telescopeUUID)

        else:
            # Do nothing
            pass

        if valid_telescope:
            self.update_payload('telescopes', [valid_telescope], 'admin')
            self.save(telescopes=json.dumps([valid_telescope]))

    def _create_night_log(self, date, local_telescope):
        result, error = self.logs_api.create({'date': date, 'telescope': local_telescope['uuid']})
        if error:
            if self.context.debug: print(str(error))
            msg = f'Failed to create night log for date {date}. Retry is automatic.'
            self.update_payload('message', msg, 'admin')
        else:
            self.save(night_log=json.dumps(result))
            self.update_payload('night_log', result, 'admin')

    def sync_night_log(self):
        local_telescope = json.loads(self.read('telescope') or '{}')
        if not local_telescope:
            return

        self.update_payload('date', self.current_date, 'admin')
        local_nightlog = json.loads(self.read('night_log') or '{}')
        self.save(datasets='')

        if local_nightlog:
            if local_nightlog['date'] == self.current_date:
                self.update_payload('night_log', local_nightlog, 'admin')
            else:
                self._create_night_log(self.current_date, local_telescope)
        else:
            logs, error = self.logs_api.list(date=self.current_date)

            if error:
                if self.context.debug: print(str(error))
                self.update_payload('message', str(error), 'admin')
            elif len(logs) == 0:
                self._create_night_log(self.current_date, local_telescope)
            elif len(logs) == 1:
                self.save(night_log=json.dumps(logs[0]))
                self.update_payload('night_log', logs[0], 'admin')
            else:
                msg = f'Multiple logs found for date {self.current_date}'
                if self.context.debug: print(msg)
                self.update_payload('message', msg, 'admin')
