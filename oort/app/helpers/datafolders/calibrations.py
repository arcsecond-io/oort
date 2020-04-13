import os

from arcsecond import Arcsecond

from .filewalkers import FilesWalker


class FiltersFolder(FilesWalker):
    # A folder of Filters folders (no files)
    def reset(self):
        self.filters = []

    def walk(self):
        for name, path in self._walk_folder():
            if not os.path.isdir(path):
                continue
            self.filters.append(FilesWalker(self.context, path, self.prefix))
        for filter in self.filters:
            filter.walk()

    def sync_flats(self, api, **kwargs):
        calibs_list = []
        datasets_list = []

        api_datasets = Arcsecond.build_datasets_api(debug=self.context.debug,
                                                    organisation=self.context.organisation)

        for flat_filter in self.filters:
            kwargs.update(type="Flats")
            kwargs.update(name=flat_filter.name)
            flat_calib = flat_filter.sync_resource('Flats ' + flat_filter.name, api, **kwargs)
            if flat_calib:
                calibs_list.append(flat_calib)

                flat_dataset = flat_filter.sync_resource('Dataset',
                                                         api_datasets,
                                                         calibration=flat_calib['uuid'],
                                                         name=flat_filter.name,
                                                         organisation=self.context.organisation)

                if flat_dataset:
                    datasets_list.append(flat_dataset)

        return calibs_list, datasets_list


class CalibrationsFolder(FilesWalker):
    # A folder of files and Biases, Darks and Flats folders

    def __init__(self, context, folderpath):
        super().__init__(context, folderpath)
        self.walk()

    def reset(self):
        self.biases_folder = None
        self.darks_folder = None
        self.flats_folders = None

    def walk(self):
        self.reset()
        for name, path in self._walk_folder():
            if os.path.isdir(path) and name.lower().startswith('bias'):
                self.biases_folder = FilesWalker(self.context, path)
                self.biases_folder.walk()
            elif os.path.isdir(path) and name.lower().startswith('dark'):
                self.darks_folder = FilesWalker(self.context, path)
                self.darks_folder.walk()
            elif os.path.isdir(path) and name.lower().startswith('flat'):
                self.flats_folders = FiltersFolder(self.context, path, 'Flats')
                self.flats_folders.walk()
            else:
                pass
                # self.files.append(path)

    def sync_resources(self, payload_key, **kwargs):
        calibrations = []
        datasets = []

        api_calibrations = Arcsecond.build_calibrations_api(debug=self.context.debug,
                                                            organisation=self.context.organisation)

        api_datasets = Arcsecond.build_datasets_api(debug=self.context.debug,
                                                    organisation=self.context.organisation)

        if self.biases_folder:
            kwargs.update(type="Biases")
            biases_calib = self.biases_folder.sync_resource("Biases", api_calibrations, **kwargs)

            if biases_calib:
                calibrations.append(biases_calib)
                biases_dataset = self.biases_folder.sync_resource('Dataset',
                                                                  api_datasets,
                                                                  calibration=biases_calib['uuid'],
                                                                  name=biases_calib['type'],
                                                                  organisation=self.context.organisation)
                if biases_dataset:
                    datasets.append(biases_dataset)

        if self.darks_folder:
            kwargs.update(type="Darks")
            darks_calib = self.darks_folder.sync_resource("Darks", api_calibrations, **kwargs)

            if darks_calib:
                calibrations.append(darks_calib)
                darks_dataset = self.darks_folder.sync_resource('Dataset',
                                                                api_datasets,
                                                                calibration=darks_calib['uuid'],
                                                                name=darks_calib['type'],
                                                                organisation=self.context.organisation)
                if darks_dataset:
                    datasets.append(darks_dataset)

        if self.flats_folders:
            flats_calibs, flats_datasets = self.flats_folders.sync_flats(api_calibrations, **kwargs)
            calibrations += flats_calibs
            datasets += flats_datasets

        self.context.payload_group_update(payload_key, calibrations=calibrations)
        self.context.payload_group_update(payload_key, datasets=datasets)
