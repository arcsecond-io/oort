import os

from .filewalkers import FilesWalker
from .calibrations import CalibrationsFolder
from .targets import TargetFolder


class TelescopeFolder(FilesWalker):
    # A folder of calibrations folders and target folders (no files)

    def __init__(self, uuid, context, folderpath):
        super().__init__(context, folderpath)
        self.uuid = uuid
        # Do NOT auto-walk.

    def reset(self):
        self.calibrations_folder = None
        self.target_folders = []

    def walk(self):
        self.reset()
        for name, path in self._walk_folder():
            if not os.path.isdir(path):
                # If not a directory, skip it. Will skip __oort__.ini files too.
                continue
            if name.lower().startswith('calib'):
                self.calibrations_folder = CalibrationsFolder(self.context, path)
            # We may wish to check for Biases, Darks etc at that level too...
            else:
                self.target_folders.append(TargetFolder(self.context, path))

    def sync_calibrations(self, payload_key, **kwargs):
        if self.calibrations_folder is None:
            return

        self.calibrations_folder.sync_biases_darks_flats(payload_key, **kwargs)
