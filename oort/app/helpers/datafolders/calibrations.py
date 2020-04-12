import os

from arcsecond import Arcsecond
from oort.app.helpers.datafolders.filewalkers import FilesWalker


class FiltersFolder(FilesWalker):
    # A folder of Filters folders (no files)

    def reset(self):
        self.filters = []

    def walk(self):
        for name, path in self._walk_folder():
            if not os.path.isdir(path):
                continue
            self.filters.append(FilesWalker(self.context, path))
        for filter in self.filters:
            filter.walk()


class CalibrationsFolder(FilesWalker):
    # A folder of files and Biases, Darks and Flats folders

    def __init__(self, context, folderpath):
        super().__init__(context, folderpath)
        self.walk()

    def reset(self):
        self.biases = None
        self.darks = None
        self.flats = []

    def walk(self):
        self.reset()
        for name, path in self._walk_folder():
            if os.path.isdir(path) and name.lower().startswith('bias'):
                self.biases = FilesWalker(self.context, path)
                self.biases.walk()
            elif os.path.isdir(path) and name.lower().startswith('dark'):
                self.darks = FilesWalker(self.context, path)
                self.darks.walk()
            elif os.path.isdir(path) and name.lower().startswith('flat'):
                self.flats = FiltersFolder(self.context, path)
                self.flats.walk()
            else:
                pass
                # self.files.append(path)
