import os

from .filters import FiltersFolder
from .filesfoldersyncer import FilesFolderSyncer


class CalibrationsFolder(FilesFolderSyncer):
    def __init__(self, context, astronomer, folderpath, prefix=''):
        self.biases_folders = []
        self.darks_folders = []
        self.flats_folders = []
        super().__init__(context, astronomer, folderpath, prefix=prefix)

    def reset(self):
        super().reset()
        self.biases_folders = []
        self.darks_folders = []
        self.flats_folders = []

    def walk(self):
        super().walk()

        for name, path in self._walk_folder():
            if os.path.isdir(path) and name.lower().startswith('bias'):
                if self.context.debug or self.context.verbose: print(f' >> Found a {self.prefix} {name} folder.')
                self.biases_folders.append(FilesFolderSyncer(self.context, self.astronomer, path))
            elif os.path.isdir(path) and name.lower().startswith('dark'):
                if self.context.debug or self.context.verbose: print(f' >> Found a {self.prefix} {name} folder.')
                self.darks_folders.append(FilesFolderSyncer(self.context, self.astronomer, path))
            elif os.path.isdir(path) and name.lower().startswith('flat'):
                if self.context.debug or self.context.verbose: print(f' >> Found a {name} folder.')
                self.flats_folders.append(FiltersFolder(self.context, self.astronomer, path, '[Flats]'))

        for bias_folder in self.biases_folders:
            bias_folder.walk()
        for darks_folder in self.darks_folders:
            darks_folder.walk()
        for flats_folder in self.flats_folders:
            flats_folder.walk()

    def upload(self, telescope_key):
        if self.context.verbose:
            print(f'Syncing calibrations for {telescope_key}')

        own_kwargs = {}
        own_kwargs.update(name=self.name)
        self.upload_files(telescope_key, 'calibrations', **own_kwargs)

        for bias_folder in self.biases_folders:
            if self.context.debug or self.context.verbose: print(f'Uploading {bias_folder.name}...')
            bias_folder.upload_files(telescope_key, 'calibrations', type='Biases', name=bias_folder.name)

        for darks_folder in self.darks_folders:
            if self.context.debug or self.context.verbose: print(f'Uploading {darks_folder.name}...')
            darks_folder.upload_files(telescope_key, 'calibrations', type='Darks', name=darks_folder.name)

        for flats_folder in self.flats_folders:
            if self.context.debug or self.context.verbose: print(f'Uploading Flats (filters)...')
            flats_folder.upload_filters(telescope_key, 'calibrations', type='Flats')
