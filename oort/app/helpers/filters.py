import copy
import os

from .filesfoldersyncer import FilesFolderSyncer


class FiltersFolder(FilesFolderSyncer):
    def __init__(self, context, astronomer, folderpath, prefix=''):
        self.filter_folders = []
        super().__init__(context, astronomer, folderpath, prefix=prefix)

    def walk(self):
        super().walk()

        known_folderpaths = [f.folderpath for f in self.filter_folders]
        for name, path in self._walk_folder():
            if os.path.isdir(path) and path not in known_folderpaths:
                if self.context.debug: print(f' >>> Found a {self.prefix} {name} folder.')
                self.filter_folders.append(FilesFolderSyncer(self.context, self.astronomer, path, self.prefix))

        for filter_folder in self.filter_folders:
            filter_folder.walk()

    def upload_filters(self, telescope_key, resources_key, **kwargs):
        if self.context.verbose:
            print(f'Syncing filters {resources_key} for {telescope_key}')

        own_kwargs = copy.deepcopy(kwargs)
        own_kwargs.update(name=self.name)
        if resources_key == 'observations':
            own_kwargs.update(target_name=self.name)
        yield from self.upload_files(telescope_key, resources_key, **own_kwargs)

        for filter_folder in self.filter_folders:
            filter_kwargs = copy.deepcopy(kwargs)
            filter_kwargs.update(name=self.name)
            if resources_key == 'observations':
                filter_kwargs.update(target_name=self.name)
            yield from filter_folder.upload_files(telescope_key, resources_key, **filter_kwargs)
