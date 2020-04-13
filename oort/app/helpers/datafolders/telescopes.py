import os

from .filewalkers import FilesWalker
from .calibrations import CalibrationsFolder
from .filters import FiltersFolder


class TelescopeFolder(FilesWalker):
    # A folder of calibrations folders and target folders (no files)

    def __init__(self, uuid, context, folderpath):
        self.uuid = uuid
        super().__init__(context, folderpath, '', auto_walk=False)
        # Do NOT auto-walk.

    def reset(self):
        self.calibrations_folders = []
        self.targets_folders = []

    def walk(self):
        self.reset()
        for name, path in self._walk_folder():
            if not os.path.isdir(path):
                # If not a directory, skip it. Will skip __oort__.ini files too.
                continue
            if name.lower().startswith('calib'):
                if self.context.debug: print(f' > Found a {self.prefix} {name} folder.')
                self.calibrations_folders.append(CalibrationsFolder(self.context, path, name))
            # We may wish to check for Biases, Darks etc at that level too...
            else:
                # Prefix Observation and Datasets names with target name.
                if self.context.debug: print(f' > Found a {self.prefix} {name} folder.')
                self.targets_folders.append(FiltersFolder(self.context, path, name))

    @property
    def payload_key(self):
        return f'telescope_{self.uuid}'

    def sync_calibrations_folders(self, payload_key, **kwargs):
        for calibrations_folder in self.calibrations_folders:
            calibrations_folder.sync_biases_darks_flats(self.payload_key, **kwargs)

    def sync_targets_folders(self, **kwargs):
        observations = []
        datasets = []

        for targets_folder in self.targets_folders:
            targets_observations, targets_datasets = targets_folder.sync_filters(self.payload_key, **kwargs)
            observations += targets_observations
            datasets += targets_datasets

        self.context.payload_group_update(self.payload_key, observations=observations)
        self.context.payload_group_update(self.payload_key, observations_datasets=datasets)

    def uploads_calibrations_folders(self):
        for calibrations_folder in self.calibrations_folders:
            calibrations_folder.upload_biases_darks_flats(self.payload_key)

    def uploads_targets_folders(self):
        for targets_folder in self.targets_folders:
            targets_folder.upload_biases_darks_flats(self.payload_key)
