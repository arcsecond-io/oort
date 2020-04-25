import os

from arcsecond import Arcsecond

from .filewalker import FilesWalker
from .calibrations import CalibrationsFolder
from .filters import FiltersFolder


class TelescopeFolder(FilesWalker):
    # A folder of calibrations folders and target folders (no files)

    def __init__(self, uuid, context, astronomer, folderpath):
        self.uuid = uuid
        self.astronomer = astronomer
        super().__init__(context, astronomer, folderpath, '')

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
            else:
                # Prefix Observation and Datasets names with target name.
                if self.context.debug: print(f' > Found a {self.prefix} {name} folder.')
                self.observations_folders.append(FiltersFolder(self.context, self.astronomer, path, name))

    @property
    def telescope_key(self):
        return f'telescope_{self.uuid}'

    def read_remote_telescope(self):
        telescopes_api = Arcsecond.build_telescopes_api(**self.api_kwargs)
        response_detail, error = telescopes_api.read(self.uuid)
        if response_detail:
            self.context.payload_append(telescopes=response_detail)
        else:
            msg = f'Unknown telescope with UUID {self.uuid}'
            self.context.payload_group_update('messages', warning=msg)

    def uploads_calibrations_folders(self):
        for calibrations_folder in self.calibrations_folders:
            calibrations_folder.upload_biases_darks_flats(self.telescope_key)

    def uploads_observations_folders(self):
        for observations_folder in self.observations_folders:
            observations_folder.upload_filters(self.telescope_key, 'observations')
