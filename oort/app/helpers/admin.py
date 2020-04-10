import json

from arcsecond import Arcsecond

from .models import RootFilesWalker
from .state import LocalState


class AdminLocalState(LocalState):
    def __init__(self, config):
        super().__init__(config)
        self.update_payload('admin', self.context.to_dict())

        self.walker = RootFilesWalker(self.current_date, self.context.folder)

        self.telescopes_api = Arcsecond.build_telescopes_api(debug=self.context.debug,
                                                             organisation=self.context.organisation)

        self.logs_api = Arcsecond.build_nightlogs_api(debug=self.context.debug,
                                                      organisation=self.context.organisation)

    def refresh(self):
        self.walker.walk()
        # Do not walk inside telescopes.
        if self.context.debug: print(f'Found telescopes: {self.walker.telescopes}')

    def sync_telescopes(self):
        valid_telescopes = []

        for telescope in self.walker.telescopes:
            valid_telescope = self._check_existing_remote_resource('Telescope',
                                                                   self.telescopes_api,
                                                                   telescope.uuid)

            if valid_telescope:
                valid_telescopes.append(valid_telescope)

        if self.context.debug: print(f'Validated telescopes: {valid_telescopes}')
        self.update_payload('telescopes', valid_telescopes, 'admin')
        self.save(telescopes=json.dumps(valid_telescopes))

        if len(valid_telescopes) == 0:
            msg = 'Restart Oort command and either provide telescope UUID with -t parameter or organisation subdomain with -o parameter.'
            self.update_payload('warning', msg, 'admin')

    # def sync_single_telescope(self):
    #     self.update_payload('message', '', 'admin')
    #     local_telescope = json.loads(self.read('telescope') or '{}')
    #     valid_telescope = None
    #
    #     if local_telescope and self.context.telescopeUUID:
    #         # Check if they are the same
    #         if local_telescope['uuid'] == self.context.telescopeUUID:
    #             self.update_payload('telescopes', [local_telescope], 'admin')
    #         else:
    #             # If not, telescope provided in CLI takes precedence, even if it fails...
    #             valid_telescope = self._check_remote_telescope(local_telescope['uuid'])
    #
    #     elif local_telescope and not self.context.telescopeUUID:
    #         self.update_payload('telescopes', [local_telescope], 'admin')
    #
    #     elif not local_telescope and self.context.telescopeUUID:
    #         valid_telescope = self._check_remote_telescope(self.context.telescopeUUID)
    #
    #     else:
    #         # Do nothing
    #         pass
    #
    #     if valid_telescope:
    #         self.update_payload('telescopes', [valid_telescope], 'admin')
    #         self.save(telescopes=json.dumps([valid_telescope]))

    # def _create_remote_night_log(self, date, telescope):
    #     response_log, error = self.logs_api.create({'date': date, 'telescope': telescope['uuid']})
    #     if error:
    #         if self.context.debug: print(str(error))
    #         msg = f'Failed to create night log for date {date}. Retry is automatic.'
    #         self.update_payload('message', msg, 'admin')
    #     else:
    #         return response_log

    def sync_night_logs(self):
        local_telescopes = json.loads(self.read('telescopes') or '[]')
        if len(local_telescopes) == 0:
            # Telescopes not yet synced. Do nothing.
            return

        self.update_payload('date', self.current_date, 'admin')

        local_logs = []
        for local_telescope in local_telescopes:
            new_log = self._find_or_create_remote_resource('Night Log',
                                                           self.logs_api,
                                                           date=self.current_date,
                                                           telescope=local_telescope['uuid'])

            if new_log:
                local_logs.append(new_log)

        if self.context.debug: print(f'Validated night logs: {local_logs}')
        self.save(night_logs=json.dumps(local_logs))
        self.update_payload('night_logs', local_logs, 'admin')

    # def sync_single_night_log(self, telescope):
    #     local_telescope = json.loads(self.read('telescope') or '{}')
    #     if not local_telescope:
    #         return
    #
    #     self.update_payload('date', self.current_date, 'admin')
    #     local_nightlog = json.loads(self.read('night_log') or '{}')
    #     self.save(datasets='')
    #
    #     if local_nightlog:
    #         if local_nightlog['date'] == self.current_date:
    #             self.update_payload('night_log', local_nightlog, 'admin')
    #         else:
    #             self._check_remote_night_log(self.current_date, local_telescope)
    #     else:
    #         logs, error = self.logs_api.list(date=self.current_date)
    #
    #         if error:
    #             if self.context.debug: print(str(error))
    #             self.update_payload('message', str(error), 'admin')
    #         elif len(logs) == 0:
    #             self._check_remote_night_log(self.current_date, local_telescope)
    #         elif len(logs) == 1:
    #             self.save(night_log=json.dumps(logs[0]))
    #             self.update_payload('night_log', logs[0], 'admin')
    #         else:
    #             msg = f'Multiple logs found for date {self.current_date}'
    #             if self.context.debug: print(msg)
    #             self.update_payload('message', msg, 'admin')
