import os

from arcsecond import Arcsecond

from .filewalkers import FilesWalker
from .calibrations import CalibrationsFolder
from .filters import FiltersFolder


class TelescopeFolder(FilesWalker):
    # A folder of calibrations folders and target folders (no files)

    def __init__(self, uuid, astronomer, context, folderpath):
        self.uuid = uuid
        self.astronomer = astronomer
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
                self.calibrations_folders.append(CalibrationsFolder(self.context, self.astronomer, path, name))
            # We may wish to check for Biases, Darks etc at that level too...
            else:
                # Prefix Observation and Datasets names with target name.
                if self.context.debug: print(f' > Found a {self.prefix} {name} folder.')
                self.observations_folders.append(FiltersFolder(self.context, self.astronomer, path, name))

    @property
    def telescope_key(self):
        return f'telescope_{self.uuid}'

    def sync(self):
        if self.astronomer:
            telescopes_api = Arcsecond.build_telescopes_api(debug=self.context.debug,
                                                            api_key=self.astronomer[1])
        else:
            telescopes_api = Arcsecond.build_telescopes_api(debug=self.context.debug,
                                                            organisation=self.context.organisation)

        telescope = self.fetch_resource('Telescope', telescopes_api, self.uuid)
        if telescope:
            self.context.payload_append(telescopes=telescope)
        else:
            msg = f'Unknown telescope with UUID {self.uuid}'
            self.context.payload_group_update('messages', warning=msg)

    def uploads_calibrations_folders(self):
        for calibrations_folder in self.calibrations_folders:
            calibrations_folder.upload_biases_darks_flats(self.telescope_key)

    def uploads_observations_folders(self):
        pass
        # for observations_folder in self.observations_folders:
        #     # The second parameter must match the key in above self.context.payload_group_update...
        #     observations_folder.upload_filters(self.telescope_key, 'observations')
