import json

from arcsecond import Arcsecond

from .helpers import State, RootFolder

MAX_SIMULTANEOUS_UPLOADS = 3


class UploadsLocalState(State):
    def __init__(self, config):
        super().__init__(config)

        self.context.payload_group_update('state', **self.context.to_dict())
        self.context.payload_group_update('state', showTables=False)
        self.context.payload_update(current_uploads=[], finished_uploads=[])

        self.autostart = True

        self.root = RootFolder(self.context)

        self.api_datasets = Arcsecond.build_datasets_api(debug=self.context.debug,
                                                         organisation=self.context.organisation)

        self.api_observations = Arcsecond.build_observations_api(debug=self.context.debug,
                                                                 organisation=self.context.organisation)

        self.api_calibrations = Arcsecond.build_calibrations_api(debug=self.context.debug,
                                                                 organisation=self.context.organisation)

    def sync_telescopes(self):
        self.root.walk()
        self.root.sync_telescopes()
        return self.context.get_yield_string()

    def sync_night_logs(self):
        self.root.sync_night_logs()
        return self.context.get_yield_string()

    # def _get_calib_key(self, tel_uuid):
    #     return f'telescope_{tel_uuid}_calibrations'
    #
    # def _get_dataset_key(self, tel_uuid):
    #     return f'telescope_{tel_uuid}_datasets'
    #
    # def _get_flat_key(self, tel_uuid):
    #     return f'telescope_{tel_uuid}_flats'
    #
    # def sync_calibrations(self):
    #     if not self.context.can_upload:
    #         return
    #
    #     local_night_logs = json.loads(self.read('night_logs') or '[]')
    #
    #     for telescope in self.walker.telescopes:
    #         night_log = next((nl for nl in local_night_logs if nl['telescope'] == telescope.uuid), None)
    #         if night_log is None:
    #             if self.context.debug: print(f'No night log for telescope {telescope.uuid}')
    #             continue
    #
    #         local_calibs = []
    #
    #         if telescope.calibrations.biases is not None:
    #             # Word 'Biases' MUST MATCH Django model field!
    #             biases = self._find_or_create_remote_resource('Bias',
    #                                                           self.api_calibrations,
    #                                                           night_log=night_log['uuid'],
    #                                                           type='Biases')
    #             if biases:
    #                 local_calibs.append(biases)
    #
    #         if telescope.calibrations.darks is not None:
    #             # Word 'Darks' MUST MATCH Django model field!
    #             darks = self._find_or_create_remote_resource('Dark',
    #                                                          self.api_calibrations,
    #                                                          night_log=night_log['uuid'],
    #                                                          type='Darks')
    #             if darks:
    #                 local_calibs.append(darks)
    #
    #         # if self.context.debug:
    #         #     print(f'Validated telescope {telescope.uuid} calibs {local_calibs}')
    #         self.save(**{self._get_calib_key(telescope.uuid): json.dumps(local_calibs)})
    #
    #         if telescope.calibrations.flats is not None:
    #             local_flats = []
    #
    #             for filter in telescope.calibrations.flats.filters:
    #                 flat = self._find_or_create_remote_resource('Flat',
    #                                                             self.api_calibrations,
    #                                                             night_log=night_log['uuid'],
    #                                                             name=filter.name,
    #                                                             type='Flats')
    #                 if flat:
    #                     local_flats.append(flat)
    #
    #             # if self.context.debug:
    #             #     print(f'Validated telescope {telescope.uuid} flats {local_flats}')
    #             self.save(**{self._get_flat_key(telescope.uuid): json.dumps(local_flats)})
    #
    # def sync_datasets(self):
    #     if not self.context.can_upload:
    #         return
    #
    #     local_night_logs = json.loads(self.read('night_logs') or '[]')
    #
    #     for telescope in self.walker.telescopes:
    #         night_log = next((nl for nl in local_night_logs if nl['telescope'] == telescope.uuid), None)
    #         if night_log is None:
    #             if self.context.debug: print(f'No night log for telescope {telescope.uuid}')
    #             continue
    #
    #         local_datasets = []
    #         local_calibs = json.loads(self.read(self._get_calib_key(telescope.uuid)) or '[]')
    #         local_flats = json.loads(self.read(self._get_flat_key(telescope.uuid)) or '[]')
    #
    #         for local_calib in local_calibs:
    #             dataset = self._find_or_create_remote_resource('Dataset',
    #                                                            self.api_datasets,
    #                                                            calibration=local_calib['uuid'],
    #                                                            name=local_calib['type'],
    #                                                            organisation=self.context.organisation)
    #
    #             if dataset:
    #                 local_datasets.append(dataset)
    #
    #         for local_flat in local_flats:
    #             dataset = self._find_or_create_remote_resource('Dataset',
    #                                                            self.api_datasets,
    #                                                            calibration=local_flat['uuid'],
    #                                                            name=local_flat['type'] + ': ' + local_flat['name'],
    #                                                            organisation=self.context.organisation)
    #
    #             if dataset:
    #                 local_datasets.append(dataset)
    #
    #         # if self.context.debug:
    #         #     print(f'Validated telescope {telescope.uuid} datasets {local_datasets}')
    #
    #         self.save(**{self._get_dataset_key(telescope.uuid): json.dumps(local_datasets)})
    #
    # def sync_uploads(self):
    #     if not self.context.can_upload:
    #         return
    #
    #     local_night_logs = json.loads(self.read('night_logs') or '[]')
    #
    #     for telescope in self.walker.telescopes:
    #         night_log = next((nl for nl in local_night_logs if nl['telescope'] == telescope.uuid), None)
    #         if night_log is None:
    #             if self.context.debug: print(f'No night log for telescope {telescope.uuid}')
    #             continue
    #
    #         local_datasets = json.loads(self.read(self._get_dataset_key(telescope.uuid)) or '[]')
    #         local_calibs = json.loads(self.read(self._get_calib_key(telescope.uuid)) or '[]')
    #
    #         # All Biases: One Dataset
    #
    #         bias_calib = next((cal for cal in local_calibs if cal['type'] == 'Biases'), None)
    #         bias_dataset = next((ds for ds in local_datasets if ds['calibration'] == bias_calib['uuid']), None)
    #         if bias_dataset:
    #             if self.context.debug: print(f'Uploading biases...')
    #             for filepath in telescope.calibrations.biases.files:
    #                 self.process_file_upload(filepath, bias_dataset)
    #
    #         # All Darks: One Dataset
    #
    #         dark_calib = next((cal for cal in local_calibs if cal['type'] == 'Darks'), None)
    #         dark_dataset = next((ds for ds in local_datasets if ds['calibration'] == dark_calib['uuid']), None)
    #         if dark_dataset:
    #             if self.context.debug: print(f'Uploading darks...')
    #             for filepath in telescope.calibrations.darks.files:
    #                 self.process_file_upload(filepath, dark_dataset)
    #
    #         # One Flat Filter: One Dataset
    #
    #         local_flats = json.loads(self.read(self._get_flat_key(telescope.uuid)) or '[]')
    #         for flat_filter in telescope.calibrations.flats.filters:
    #             flat_calib = next((flat for flat in local_flats if flat['name'] == flat_filter.name), None)
    #             flat_dataset = next((ds for ds in local_datasets if ds['calibration'] == flat_calib['uuid']), None)
    #
    #             if flat_dataset:
    #                 if self.context.debug: print(f'Uploading flats {flat_filter.name} {flat_filter.files}...')
    #                 for filepath in flat_filter.files:
    #                     self.process_file_upload(filepath, flat_dataset)
    #
    #         current_uploads = [fw.to_dict() for fw in self.uploads.values() if fw.is_finished() is False]
    #         finished_uploads = [fw.to_dict() for fw in self.uploads.values() if fw.is_finished() is True]
    #         self.update_payload('current_uploads', current_uploads)
    #         self.update_payload('finished_uploads', finished_uploads)
    #         self.update_payload('showTables', True, 'state')
    #
    #         if self.context.debug:
    #             print(finished_uploads)
    #
    # def process_file_upload(self, filepath, dataset):
    #     fw = self.uploads.get(filepath)
    #     if fw is None:
    #         fw = FileWrapper(filepath, dataset['uuid'], dataset['name'], self.context.debug)
    #         self.uploads[filepath] = fw
    #
    #     started_count = len([u for u in self.uploads.values() if u.is_started()])
    #     if self.autostart and started_count < MAX_SIMULTANEOUS_UPLOADS:
    #         if fw.exists_remotely():
    #             fw.finish()
    #         else:
    #             fw.start()
    #
    #     if fw.will_finish():
    #         fw.finish()
