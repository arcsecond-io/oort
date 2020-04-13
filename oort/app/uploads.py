from .helpers import State, RootFolder, FileWrapper

MAX_SIMULTANEOUS_UPLOADS = 3


class UploadsLocalState(State):
    def __init__(self, config):
        super().__init__(config)
        self.context.payload_group_update('state', **self.context.to_dict())
        self.context.payload_group_update('state', showTables=False)
        self.context.payload_update(current_uploads=[], finished_uploads=[])
        self.root = RootFolder(self.context)
        self.uploads = {}
        self.autostart = True

    def sync_telescopes(self):
        self.root.walk()
        self.root.sync_telescopes()
        return self.context.get_yield_string()

    def sync_night_logs(self):
        self.root.sync_night_logs()
        return self.context.get_yield_string()

    def sync_calibrations(self):
        night_logs = self.context.get_payload('night_logs')
        for telescope_folder in self.root.telescope_folders:
            night_log = self.find(night_logs, telescope=telescope_folder.uuid)
            if night_log:
                payload_key = f'telescope_{telescope_folder.uuid}'
                telescope_folder.sync_calibrations(payload_key, night_log=night_log['uuid'])
            yield self.context.get_yield_string()

    def sync_uploads(self):
        if not self.context.can_upload:
            return

        self.context.payload_update('showTables', True, 'state')

        night_logs = self.context.get_payload('night_logs')
        for telescope_folder in self.root.telescope_folders:
            night_log = self.find(night_logs, telescope=telescope_folder.uuid)
            if not night_log:
                continue

            payload_key = f'telescope_{telescope_folder.uuid}'
            datasets = self.context.get_group_payload(payload_key, 'datasets')
            calibrations = self.context.get_group_payload(payload_key, 'calibrations')

            # All Biases: One Dataset

            bias_calib = self.find(calibrations, type='Biases')
            bias_dataset = self.find(datasets, calibration=bias_calib['uuid'])
            if bias_dataset:
                if self.context.debug: print(f'Uploading biases...')
                for filepath in telescope_folder.calibrations.biases.files:
                    self._process_file_upload(filepath, bias_dataset)

            yield self._update_context()

            # All Darks: One Dataset

            dark_calib = self.find(calibrations, type='Darks')
            dark_dataset = self.find(datasets, calibration=dark_calib['uuid'])
            if dark_dataset:
                if self.context.debug: print(f'Uploading darks...')
                for filepath in telescope_folder.calibrations.darks.files:
                    self._process_file_upload(filepath, dark_dataset)

            yield self._update_context()

            # Flats: One Dataset per Flat Filter

            flats_calibs = self.find(calibrations, type='Flats')
            for flat_filter in telescope_folder.calibrations.flats.filters:
                flat_calib = self.find(flats_calibs, name=flat_filter.name)
                flat_dataset = self.find(datasets, calibration=flat_calib['uuid'])
                if flat_dataset:
                    if self.context.debug: print(f'Uploading flats {flat_filter.name} {flat_filter.files}...')
                    for filepath in flat_filter.files:
                        self._process_file_upload(filepath, flat_dataset)

            yield self._update_context()

    def _update_context(self):
        current_uploads = [fw.to_dict() for fw in self.uploads.values() if fw.is_finished() is False]
        finished_uploads = [fw.to_dict() for fw in self.uploads.values() if fw.is_finished() is True]
        self.context.payload_update('current_uploads', current_uploads)
        self.context.payload_update('finished_uploads', finished_uploads)
        yield self.get_yield_string()

    def _process_file_upload(self, filepath, dataset):
        fw = self.uploads.get(filepath)
        if fw is None:
            fw = FileWrapper(filepath, dataset['uuid'], dataset['name'], self.context.debug)
            self.uploads[filepath] = fw

        started_count = len([u for u in self.uploads.values() if u.is_started()])
        if self.autostart and started_count < MAX_SIMULTANEOUS_UPLOADS:
            if fw.exists_remotely():
                fw.finish()
            else:
                fw.start()

        if fw.will_finish():
            fw.finish()
