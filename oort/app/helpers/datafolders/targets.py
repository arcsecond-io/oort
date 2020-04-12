import os

from arcsecond import Arcsecond

from .filewalkers import FilesWalker


class TargetFolder(FilesWalker):
    # A folder of files and Observations folders

    def __init__(self, date, folderpath):
        super().__init__(date, folderpath)
        self.walk()

    def reset(self):
        self.observation_folders = []

    def walk(self):
        self.reset()
        for name, path in self._walk_folder():
            if os.path.isdir(path):
                self.observation_folders.append(FilesWalker(self.context, path))
            else:
                self.files.append(path)

