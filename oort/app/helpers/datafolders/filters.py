import os

from .filewalker import FilesWalker
from .filesyncer import FilesSyncer


class FiltersFolder(FilesWalker):
    def reset(self):
        self.filter_folders = []

    def walk(self):
        for name, path in self._walk_folder():
            if not os.path.isdir(path):
                continue
            if self.context.debug: print(f' >  >  > Found a [{self.prefix}] {name} folder.')
            self.filter_folders.append(FilesSyncer(self.context, self.astronomer, path, self.prefix))

    def upload_filters(self, telescope_key, resources_key, **kwargs):
        for filter_folder in self.filter_folders:
            kwargs.update(name=filter_folder.name)
            filter_folder.upload_files(telescope_key, resources_key, **kwargs)
