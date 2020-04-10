import os
from configparser import ConfigParser


class FilesFolder:
    def __init__(self, date, folderpath):
        self.date = date
        self.folderpath = folderpath
        self.files = []

    @property
    def name(self):
        return os.path.basename(self.folderpath)

    def _reset(self):
        pass

    def _parse(self):
        for name, path in self._walk_filesystem(self.folderpath):
            if not os.path.exists(path) or os.path.isdir(path):
                continue
            # Todo: deal with timezones and filename formats!
            if self.date in name:
                self.files.append(path)

    def _walk_filesystem(self, folderpath):
        if not os.path.exists(folderpath) or not os.path.isdir(folderpath):
            return zip([], [])
        names = os.listdir(folderpath)
        paths = [os.path.join(folderpath, name) for name in names if len(name) > 0 and name[0] != '.']
        return zip(names, paths)


class Calibrations(FilesFolder):
    def __init__(self, date, folderpath):
        super().__init__(date, folderpath)
        self._parse()

    def _reset(self):
        self.biases = None
        self.darks = None
        self.flats = None

    def _parse(self):
        self._reset()
        for name, path in self._walk_filesystem(self.folderpath):
            if not os.path.isdir(path):
                continue
            if name.lower().startswith('bias'):
                self.biases = FilesFolder(self.date, path)
            elif name.lower().startswith('dark'):
                self.darks = FilesFolder(self.date, path)
            elif name.lower().startswith('flat'):
                self.flats = FilesFolder(self.date, path)


class Target(FilesFolder):
    def __init__(self, date, folderpath):
        super().__init__(date, folderpath)
        self._parse()

    def _reset(self):
        self.observations = []

    def _parse(self):
        self._reset()
        for name, path in self._walk_filesystem(self.folderpath):
            if not os.path.isdir(path):
                continue
            else:
                self.observations.append(FilesFolder(self.date, path))


class Telescope(FilesFolder):
    def __init__(self, uuid, date, folderpath):
        self.uuid = uuid
        super().__init__(date, folderpath)

    def _reset(self):
        self.calibrations = None
        self.targets = []

    def _parse(self):
        self._reset()
        for name, path in self._walk_filesystem(self.folderpath):
            if not os.path.isdir(path):
                # If not a directory, skip it. Will skip __oort__.ini files too.
                continue
            if name.lower().startswith('calib'):
                self.calibrations = Calibrations(self.date, path)
            else:
                self.targets.append(Target(self.date, path))


class NightLog(FilesFolder):
    def __init__(self, date, folderpath):
        super().__init__(date, folderpath)
        self._parse()

    def _reset(self):
        self.telescopes = []

    def _parse(self):
        self._reset()

        for name, path in self._walk_filesystem(self.folderpath):
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
