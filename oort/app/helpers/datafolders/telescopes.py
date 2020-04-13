import os

from arcsecond import Arcsecond

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
        self.observations_folders = []

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
                self.observations_folders.append(FiltersFolder(self.context, path, name))

    @property
    def telescope_key(self):
        return f'telescope_{self.uuid}'

    def sync_calibrations_folders(self, **kwargs):
        for calibrations_folder in self.calibrations_folders:
            calibrations_folder.sync_biases_darks_flats(self.telescope_key, **kwargs)

    def sync_observations_folders(self, **kwargs):
        observations = []
        datasets = []

        api = Arcsecond.build_observations_api(debug=self.context.debug,
                                               organisation=self.context.organisation)

        for observations_folder in self.observations_folders:
            kwargs.update(target_name=observations_folder.prefix)
            resources_list, datasets_list = observations_folder.sync_filters('Observations',
                                                                             'observation',
                                                                             api,
                                                                             **kwargs)
            observations += resources_list
            datasets += datasets_list

        self.context.payload_group_update(self.telescope_key, observations=observations)
        self.context.payload_group_update(self.telescope_key, observations_datasets=datasets)

    def uploads_calibrations_folders(self):
        for calibrations_folder in self.calibrations_folders:
            calibrations_folder.upload_biases_darks_flats(self.telescope_key)

    def uploads_observations_folders(self):
        for observations_folder in self.observations_folders:
            # The second parameter must match the key in above self.context.payload_group_update...
            observations_folder.upload_filters(self.telescope_key, 'observations')
