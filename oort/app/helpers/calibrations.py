import os

from .filters import FiltersFolder
from .filesyncer import FilesSyncer


class CalibrationsFolder(FilesSyncer):
    def reset(self):
        self.files = []
        self.biases_folders = []
        self.darks_folders = []
        self.flats_folders = []

    def walk(self):
        self.reset()
        for name, path in self._walk_folder():
            if os.path.isdir(path) and name.lower().startswith('bias'):
                if self.context.debug: print(f' >> Found a [{self.prefix}] {name} folder.')
                self.biases_folders.append(FilesSyncer(self.context, self.astronomer, path))
            elif os.path.isdir(path) and name.lower().startswith('dark'):
                if self.context.debug: print(f' >> Found a [{self.prefix}] {name} folder.')
                self.darks_folders.append(FilesSyncer(self.context, self.astronomer, path))
            elif os.path.isdir(path) and name.lower().startswith('flat'):
                if self.context.debug: print(f' >> Found a [{self.prefix}] {name} folder.')
                self.flats_folders.append(FiltersFolder(self.context, self.astronomer, path, '[Flats]'))

    def upload_biases_darks_flats(self, telescope_key):
        for bias_folder in self.biases_folders:
            if self.context.debug: print(f'Uploading {bias_folder.name}...')
            bias_folder.upload_files(telescope_key, 'calibrations', type='Biases', name=bias_folder.name)

        for darks_folder in self.darks_folders:
            if self.context.debug: print(f'Uploading {darks_folder.name}...')
            darks_folder.upload_files(telescope_key, 'calibrations', type='Darks', name=darks_folder.name)

        for flats_folder in self.flats_folders:
            if self.context.debug: print(f'Uploading Flats (filters)...')
            flats_folder.upload_filters(telescope_key, 'calibrations', type='Flats')
