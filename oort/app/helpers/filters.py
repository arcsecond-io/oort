import copy
import os

from .constants import OORT_FILENAME
from .filesyncer import FilesSyncer


class FiltersFolder(FilesSyncer):
    def reset(self):
        self.files = []
        self.filter_folders = []

    def walk(self):
        self.reset()
        for name, path in self._walk_folder():
            if os.path.isdir(path):
                if self.context.debug: print(f' >>> Found a [{self.prefix}] {name} folder.')
                self.filter_folders.append(FilesSyncer(self.context, self.astronomer, path, self.prefix))
            elif os.path.isfile(path) and name != OORT_FILENAME:
                file_date = self._get_fits_filedate(path)
                if file_date:
                    self.files.append((path, file_date))
                else:
                    if self.context.debug: f'{path} ignored, date can\'t be found inside FITS.'

    def upload_filters(self, telescope_key, resources_key, **kwargs):
        own_kwargs = copy.deepcopy(kwargs)
        own_kwargs.update(name=self.name)
        self.upload_files(telescope_key, resources_key, **own_kwargs)

        for filter_folder in self.filter_folders:
            filter_kwargs = copy.deepcopy(kwargs)
            filter_kwargs.update(name=filter_folder.name)
            filter_folder.upload_files(telescope_key, resources_key, **filter_kwargs)
