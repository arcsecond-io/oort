import copy
import os

from .filesyncer import FilesSyncer


class FiltersFolder(FilesSyncer):
    def reset(self):
        self.files = []
        self.filter_folders = []

    def walk(self):
        super().walk()
        for name, path in self._walk_folder():
            if os.path.isdir(path):
                if self.context.debug: print(f' >>> Found a [{self.prefix}] {name} folder.')
                self.filter_folders.append(FilesSyncer(self.context, self.astronomer, path, self.prefix))

    def upload_filters(self, telescope_key, resources_key, **kwargs):
        if self.context.verbose:
            print(f'Syncing filters {resources_key} for telescope {telescope_key}')

        own_kwargs = copy.deepcopy(kwargs)
        if resources_key == 'observations':
            own_kwargs.update(target_name=self.name)
        else:
            own_kwargs.update(name=self.name)
        self.upload_files(telescope_key, resources_key, **own_kwargs)

        for filter_folder in self.filter_folders:
            filter_kwargs = copy.deepcopy(kwargs)
            if resources_key == 'observations':
                filter_kwargs.update(target_name=self.name)
            else:
                filter_kwargs.update(name=self.name)
            filter_folder.upload_files(telescope_key, resources_key, **filter_kwargs)
