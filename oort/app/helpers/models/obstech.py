import os
from configparser import ConfigParser


class FilesWalker:
    def __init__(self, date, folderpath):
        self.date = date
        self.folderpath = folderpath
        self.files = []
        self.reset()

    @property
    def name(self):
        return os.path.basename(self.folderpath)

    def reset(self):
        pass

    def walk(self):
        for name, path in self._walk_folder(self.folderpath):
            if not os.path.exists(path) or os.path.isdir(path):
                continue
            # Todo: deal with timezones and filename formats!
            if self.date in name:
                self.files.append(path)

    def _walk_folder(self, folderpath):
        if not os.path.exists(folderpath) or not os.path.isdir(folderpath):
            return zip([], [])
        names = os.listdir(folderpath)
        return [(name, os.path.join(folderpath, name)) for name in names if name[0] != '.']


class Filters(FilesWalker):
    def __init__(self, date, folderpath):
        super().__init__(date, folderpath)

    def reset(self):
        self.filters = []

    def walk(self):
        for name, path in self._walk_folder(self.folderpath):
            if not os.path.isdir(path):
                continue
            self.filters.append(FilesWalker(self.date, path))


class Calibrations(FilesWalker):
    def __init__(self, date, folderpath):
        super().__init__(date, folderpath)
        self.walk()

    def reset(self):
        self.biases = None
        self.darks = None
        self.flats = []

    def walk(self):
        self.reset()
        for name, path in self._walk_folder(self.folderpath):
            if not os.path.isdir(path):
                continue
            if name.lower().startswith('bias'):
                self.biases = FilesWalker(self.date, path)
                self.biases.walk()
            elif name.lower().startswith('dark'):
                self.darks = FilesWalker(self.date, path)
                self.darks.walk()
            elif name.lower().startswith('flat'):
                self.flats = Filters(self.date, path)
                self.flats.walk()


class Target(FilesWalker):
    def __init__(self, date, folderpath):
        super().__init__(date, folderpath)
        self.walk()

    def reset(self):
        self.observations = []

    def walk(self):
        self.reset()
        for name, path in self._walk_folder(self.folderpath):
            if not os.path.isdir(path):
                continue
            self.observations.append(FilesWalker(self.date, path))


class Telescope(FilesWalker):
    def __init__(self, uuid, date, folderpath):
        self.uuid = uuid
        super().__init__(date, folderpath)
        # Do NOT auto-walk.

    def reset(self):
        self.calibrations = None
        self.targets = []

    def walk(self):
        self.reset()
        for name, path in self._walk_folder(self.folderpath):
            if not os.path.isdir(path):
                # If not a directory, skip it. Will skip __oort__.ini files too.
                continue
            if name.lower().startswith('calib'):
                self.calibrations = Calibrations(self.date, path)
            else:
                self.targets.append(Target(self.date, path))


class RootFilesWalker(FilesWalker):
    def __init__(self, date, folderpath):
        super().__init__(date, folderpath)
        self.walk()

    def reset(self):
        self.telescopes = []

    def walk(self):
        self.reset()
        for name, path in self._walk_folder(self.folderpath):
            if not os.path.exists(path) or not os.path.isdir(path):
                continue
            oort_filepath = os.path.join(path, '__oort__')
            if os.path.exists(oort_filepath) and os.path.isfile(oort_filepath):
                self._append_telescope(oort_filepath)

    def _append_telescope(self, oort_filepath):
        with open(oort_filepath, 'r') as f:
            _config = ConfigParser()
            _config.read(oort_filepath)
            if 'telescope' in _config:
                tel_uuid = _config['telescope']['uuid']
                if tel_uuid:
                    self.telescopes.append(Telescope(tel_uuid, self.date, os.path.dirname(oort_filepath)))
