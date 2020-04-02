import json
import datetime

from arcsecond import Arcsecond

from .state import LocalState


class AdminLocalState(LocalState):
    def __init__(self, config):
        super().__init__(config)
        self.update_payload('admin', self.context.to_dict())

        self.telescopes_api = Arcsecond.build_telescopes_api(debug=self.context.debug,
                                                             organisation=self.context.organisation)

        self.logs_api = Arcsecond.build_nightlogs_api(debug=self.context.debug,
                                                      organisation=self.context.organisation)

    def _check_remote_telescope(self, ):
        telescope, error = self.telescopes_api.read(self.context.telescopeUUID)
        if error:
            if self.context.debug: print(str(error))
            self.update_payload('message', str(error), 'admin')
        elif telescope:
            self.update_payload('message', '', 'admin')
            self.update_payload('telescope', telescope, 'admin')
            self.save(telescope=json.dumps(telescope))
        else:
            self.update_payload('message', f"Unknown telescope with UUID {self.context.telescopeUUID}", 'admin')
            self.save(telescope='')

    def sync_telescope(self):
        self.update_payload('message', '', 'admin')
        local_telescope = json.loads(self.read('telescope') or '{}')

        if local_telescope and self.context.telescopeUUID:
            # Check if they are the same
            if local_telescope['uuid'] == self.context.telescopeUUID:
                self.update_payload('telescope', local_telescope, 'admin')
            else:
                # If not, telescope provided in CLI takes precedence, even if it fails...
                self._check_remote_telescope()

        elif local_telescope and not self.context.telescopeUUID:
            self.update_payload('telescope', local_telescope, 'admin')

        elif not local_telescope and self.context.telescopeUUID:
            self._check_remote_telescope()

        else:
            # Do nothing
            pass

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

        before_noon = datetime.datetime.now().hour < 12
        if before_noon:
            date = (datetime.datetime.now() - datetime.timedelta(days=1)).date().isoformat()
        else:
            date = datetime.datetime.now().date().isoformat()

        self.update_payload('date', date, 'admin')
        local_nightlog = json.loads(self.read('night_log') or '{}')
        self.save(datasets='')

        if local_nightlog:
            if local_nightlog['date'] == date:
                self.update_payload('night_log', local_nightlog, 'admin')
            else:
                self._create_night_log(date, local_telescope)
        else:
            logs, error = self.logs_api.list(date=date)

            if error:
                if self.context.debug: print(str(error))
                self.update_payload('message', str(error), 'admin')
            elif len(logs) == 0:
                self._create_night_log(date, local_telescope)
            elif len(logs) == 1:
                self.save(night_log=json.dumps(logs[0]))
                self.update_payload('night_log', logs[0], 'admin')
            else:
                msg = f'Multiple logs found for date {date}'
                if self.context.debug: print(msg)
                self.update_payload('message', msg, 'admin')
