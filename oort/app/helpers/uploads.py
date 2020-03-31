import os
from arcsecond import Arcsecond

from .state import LocalState

#
# def wrap_files(debug, folder, dataset_uuid, autostart=True):
#     files = os.listdir(folder)
#     for file in files:
#         filepath = os.path.join(folder, file)
#         fw = UPLOADS.get(filepath)
#         if fw is None:
#             fw = FileWrapper(filepath, dataset_uuid, debug)
#             UPLOADS[filepath] = fw
#
#         started_count = len([u for u in UPLOADS.values() if u.is_started()])
#         if autostart and started_count < MAX_SIMULTANEOUS_UPLOADS:
#             fw.start()
#         if fw.will_finish():
#             fw.finish()


ROOT_FILES_SECTION = '__root__'


class UploadsLocalState(LocalState):
    def __init__(self, config):
        super().__init__(config)
        self.update_payload('state', self.context.to_dict())
        self.update_payload('showTables', False, 'state')
        self.update_payload('current_uploads', [])
        self.update_payload('finished_uploads', [])

        self.files = {}
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
        if not self.context.canUpload:
            return

        local_nightlog = self.read('night_log')
        if not local_nightlog:
            return

        self._read_local_files(ROOT_FILES_SECTION)
        print(self.files)

        # api_datasets = Arcsecond.build_datasets_api(debug=debug)
        # all_datasets = api_datasets.list()
        # upload_dataset = next((d for d in all_datasets if d['name'] == DATASET_NAME), None)
        # if not upload_dataset:
        #     msg = f'Dataset "{DATASET_NAME}" does not exist. Creating it...'
        #     state = {'message': msg, 'showTables': False}
        #     json_data = json.dumps({'state': state, 'uploads': [], 'finished_uploads': []})
        #     yield f"data:{json_data}\n\n"
        #     upload_dataset = api_datasets.create({'name': DATASET_NAME})
        # else:
        #     msg = f'Dataset "{DATASET_NAME}" exists. Walking through local files...'
        #     state = {'message': msg, 'showTables': False}
        #     json_data = json.dumps({'state': state, 'uploads': [], 'finished_uploads': []})
        #     yield f"data:{json_data}\n\n"
        #
        # while True:
        #     wrap_files(debug, folder, upload_dataset['uuid'])
        #     uploads_data = [fw.to_dict() for fw in UPLOADS.values() if fw.is_finished() is False]
        #     finished_uploads_data = [fw.to_dict() for fw in UPLOADS.values() if fw.is_finished() is True]
        #     state = {'message': '', 'showTables': True}
        #     json_data = json.dumps(
        #         {'state': state, 'uploads': uploads_data, 'finished_uploads': finished_uploads_data})
