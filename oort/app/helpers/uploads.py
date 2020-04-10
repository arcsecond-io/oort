import json

import arcsecond
from arcsecond import Arcsecond

from .filewrapper import FileWrapper
from .models import RootFilesWalker
from .state import LocalState

ROOT_FILES_SECTION = '__oort__'
MAX_SIMULTANEOUS_UPLOADS = 3


class UploadsLocalState(LocalState):
    def __init__(self, config):
        super().__init__(config)
        self.update_payload('state', self.context.to_dict())
        self.update_payload('showTables', False, 'state')
        self.update_payload('current_uploads', [])
        self.update_payload('finished_uploads', [])

        self.files = {}
        self.uploads = {}
        self.autostart = True

        self.walker = RootFilesWalker(self.current_date, self.context.folder)

        self.api_datasets = Arcsecond.build_datasets_api(debug=self.context.debug,
                                                         organisation=self.context.organisation)

        self.api_observations = Arcsecond.build_observations_api(debug=self.context.debug,
                                                                 organisation=self.context.organisation)

        self.api_calibrations = Arcsecond.build_calibrations_api(debug=self.context.debug,
                                                                 organisation=self.context.organisation)

    def refresh(self):
        self.walker.walk()
        for telescope in self.walker.telescopes:
            telescope.walk()

    def sync_calibrations(self):
        if not self.context.can_upload:
            return

        local_night_logs = json.loads(self.read('night_logs') or '[]')
        local_calibs = []

        for telescope in self.walker.telescopes:
            night_log = next((nl for nl in local_night_logs if nl['telescope'] == telescope['uuid']), None)
            if night_log is None:
                continue

            for calibration in telescope.calibrations:
                # Word 'Biases' MUST MATCH Django model field!
                biases = self._find_or_create_remote_resource('Bias',
                                                              self.api_calibrations,
                                                              night_log=night_log['uuid'],
                                                              type='Biases')
                if biases:
                    local_calibs.append(biases)

                # Word 'Darks' MUST MATCH Django model field!
                darks = self._find_or_create_remote_resource('Dark',
                                                             self.api_calibrations,
                                                             night_log=night_log['uuid'],
                                                             type='Darks')
                if darks:
                    local_calibs.append(darks)

    def sync_datasets(self):
        if not self.context.can_upload:
            return

        return

        self._read_local_files(ROOT_FILES_SECTION)
        local_datasets = json.loads(self.read('datasets') or '{}')
        new_local_datasets = {}

        for dataset_name in self.files.keys():
            if dataset_name in local_datasets.values():
                # Ok, remote dataset with name exists, find its key (uuid).
                dataset_uuid = dict((v, k) for k, v in local_datasets.items())[dataset_name]
                new_local_datasets[dataset_uuid] = dataset_name
            else:
                night_log_uuid = local_nightlog.get('uuid')
                try:
                    existing_datasets_response, error = self.api_datasets.list(name=dataset_name,
                                                                               night_log=night_log_uuid)
                except arcsecond.api.error.ArcsecondConnectionError as e:
                    if self.context.debug: print(str(e))
                    self.update_payload('warning', str(e), 'state')
                else:
                    self.update_payload('warning', '', 'state')
                    existing_datasets = existing_datasets_response['results']
                    if error:
                        if self.context.debug: print(str(error))
                    elif len(existing_datasets) == 0:
                        payload = {'name': dataset_name, 'night_log': local_nightlog.get('uuid')}
                        result, error = self.api_datasets.create(payload)
                        if error:
                            if self.context.debug: print(str(error))
                        elif result:
                            new_local_datasets[result['uuid']] = dataset_name
                    elif len(existing_datasets) == 1:
                        new_local_datasets[existing_datasets[0]['uuid']] = dataset_name
                    else:
                        msg = f'Multiple datasets found for name {dataset_name}. Choosing first created one.'
                        if self.context.debug: print(str(error))
                        self.update_payload('warning', msg, 'state')
                        existing_datasets.sort(key=lambda obj: obj['creation_date'])
                        new_local_datasets[existing_datasets[0]['uuid']] = dataset_name

        self.save(datasets=json.dumps(new_local_datasets))

    def sync_uploads(self):
        if not self.context.can_upload:
            return

        return

        local_nightlog = json.loads(self.read('night_log') or '{}')
        if not local_nightlog:
            return

        self._read_local_files(ROOT_FILES_SECTION)
        local_datasets = json.loads(self.read('datasets') or '{}')

        self.update_payload('showTables', True, 'state')

        for dataset_name in self.files.keys():
            if dataset_name in local_datasets.values():
                dataset_uuid = dict((v, k) for k, v in local_datasets.items())[dataset_name]

                for filepath in self.files[dataset_name]:
                    fw = self.uploads.get(filepath)
                    if fw is None:
                        fw = FileWrapper(filepath, dataset_uuid, dataset_name, self.context.debug)
                        self.uploads[filepath] = fw

                    started_count = len([u for u in self.uploads.values() if u.is_started()])
                    if self.autostart and started_count < MAX_SIMULTANEOUS_UPLOADS:
                        fw.start()
                    if fw.will_finish():
                        fw.finish()

                current_uploads = [fw.to_dict() for fw in self.uploads.values() if fw.is_finished() is False]
                finished_uploads = [fw.to_dict() for fw in self.uploads.values() if fw.is_finished() is True]
                self.update_payload('current_uploads', current_uploads)
                self.update_payload('finished_uploads', finished_uploads)

            else:
                # Wait for sync datasets to get the dataset for that folder
                pass
