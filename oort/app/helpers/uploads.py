import json
import os
from arcsecond import Arcsecond

from .filewrapper import FileWrapper
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

        self.api_datasets = Arcsecond.build_datasets_api(debug=self.context.debug,
                                                         organisation=self.context.organisation)

    def _read_local_files(self, section):
        suffix = section if section != ROOT_FILES_SECTION else ''
        names = os.listdir(os.path.join(self.context.folder, suffix))
        for name in names:
            path = os.path.join(self.context.folder, name)
            if os.path.isdir(path):
                if section == ROOT_FILES_SECTION:
                    self._read_local_files(name)
            else:
                if section not in self.files.keys():
                    self.files[section] = []
                if len(name) > 0 and name[0] != '.' and path not in self.files[section] and os.path.isfile(path):
                    self.files[section].append(path)

    def sync_datasets(self):
        if not self.context.can_upload:
            return

        local_nightlog = json.loads(self.read('night_log') or '{}')
        if not local_nightlog:
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
                existing_datasets, error = self.api_datasets.list(name=dataset_name, night_log=night_log_uuid)
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
                    self.update_payload('message', msg)
                    existing_datasets.sort(key=lambda obj: obj['creation_date'])
                    new_local_datasets[existing_datasets[0]['uuid']] = dataset_name

        self.save(datasets=json.dumps(new_local_datasets))

    def sync_uploads(self):
        if not self.context.can_upload:
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
