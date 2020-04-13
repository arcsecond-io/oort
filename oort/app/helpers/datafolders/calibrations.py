import os

from arcsecond import Arcsecond

from .filewalkers import FilesWalker
from .filters import FiltersFolder
from .utils import find


class CalibrationsFolder(FilesWalker):
    def reset(self):
        self.biases_folders = []
        self.darks_folders = []
        self.flats_folders = []

    def walk(self):
        self.reset()
        for name, path in self._walk_folder():
            if os.path.isdir(path) and name.lower().startswith('bias'):
                if self.context.debug: print(f' >  > Found a [{self.prefix}] {name} folder.')
                self.biases_folders.append(FilesWalker(self.context, path, self.prefix))
            elif os.path.isdir(path) and name.lower().startswith('dark'):
                if self.context.debug: print(f' >  > Found a [{self.prefix}] {name} folder.')
                self.darks_folders.append(FilesWalker(self.context, path, self.prefix))
            elif os.path.isdir(path) and name.lower().startswith('flat'):
                if self.context.debug: print(f' >  > Found a [{self.prefix}] {name} folder.')
                self.flats_folders.append(FiltersFolder(self.context, path, self.prefix + ' Flats'))

    def sync_biases_darks_flats(self, telescope_key, **kwargs):
        calibrations_list = []
        datasets_list = []

        api = Arcsecond.build_calibrations_api(debug=self.context.debug,
                                               organisation=self.context.organisation)

        for bias_folder in self.biases_folders:
            kwargs.update(type="Biases")
            kwargs.update(name=bias_folder.name)
            biases_calib, biases_dataset = bias_folder.sync_resource_pair("Biases", 'calibration', api, **kwargs)

            if biases_calib:
                calibrations_list.append(biases_calib)
            if biases_dataset:
                datasets_list.append(biases_dataset)

        for darks_folder in self.darks_folders:
            kwargs.update(type="Darks")
            kwargs.update(name=darks_folder.name)
            darks_calib, darks_dataset = darks_folder.sync_resource_pair("Darks", 'calibration', api, **kwargs)

            if darks_calib:
                calibrations_list.append(darks_calib)
            if darks_dataset:
                datasets_list.append(darks_dataset)

        for flats_folder in self.flats_folders:
            kwargs.update(type="Flats")
            flats_calibs, flats_datasets = flats_folder.sync_filters("Flats", 'calibration', api, **kwargs)
            calibrations_list += flats_calibs
            datasets_list += flats_datasets

        self.context.payload_group_update(telescope_key, calibrations=calibrations_list)
        self.context.payload_group_update(telescope_key, calibrations_datasets=datasets_list)

    def upload_biases_darks_flats(self, telescope_key):
        self._upload_biases_darks(telescope_key)
        self._upload_flats(telescope_key)

    def _upload_biases_darks(self, telescope_key):
        # The second parameter must match the key in above self.context.payload_group_update...
        # Todo refactor to uniformize the level at whicb payload is updated.
        calibrations = self.context.get_group_payload(telescope_key, 'calibrations')
        calibrations_datasets = self.context.get_group_payload(telescope_key, 'calibrations_datasets')

        if not calibrations_datasets or not calibrations:
            return

        for bias_folder in self.biases_folders:
            bias_calib = find(calibrations, type='Biases', name=bias_folder.name)
            if bias_calib:
                bias_dataset = find(calibrations_datasets, calibration=bias_calib['uuid'])
                if bias_dataset:
                    if self.context.debug: print(f'Uploading {bias_folder.name}...')
                    bias_folder.upload_files(bias_dataset)

        for darks_folder in self.darks_folders:
            dark_calib = find(calibrations, type='Biases', name=darks_folder.name)
            if dark_calib:
                dark_dataset = find(calibrations_datasets, calibration=dark_calib['uuid'])
                if dark_dataset:
                    if self.context.debug: print(f'Uploading {darks_folder.name}...')
                    darks_folder.upload_files(dark_dataset)

    def _upload_flats(self, telescope_key):
        for flats_folder in self.flats_folders:
            # The second parameter must match the key in above self.context.payload_group_update...
            flats_folder.upload_filters(telescope_key, 'calibrations')
