import copy
import os

from .filesfoldersyncer import FilesFolderSyncer


class FiltersFolder(FilesFolderSyncer):
    def __init__(self, context, astronomer, folderpath, prefix=''):
        self.filter_folders = []
        super().__init__(context, astronomer, folderpath, prefix=prefix)

    def reset(self):
        super().reset()
        self.filter_folders = []

    def walk(self):
        super().walk()

        for name, path in self._walk_folder():
            if os.path.isdir(path):
                if self.context.debug: print(f' >>> Found a {self.prefix} {name} folder.')
                self.filter_folders.append(FilesFolderSyncer(self.context, self.astronomer, path, self.prefix))

        for filter_folder in self.filter_folders:
            filter_folder.walk()

    def upload_filters(self, telescope_key, resources_key, **kwargs):
        if self.context.verbose:
            print(f'Syncing filters {resources_key} for {telescope_key}')

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
