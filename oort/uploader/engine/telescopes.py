import os

from arcsecond import Arcsecond

from .filesfolder import FilesFolder
from .calibrations import CalibrationsFolder
from .filters import FiltersFolder


class TelescopeFolder(FilesFolder):
    # A folder of calibrations folders and target folders (no files)

    def __init__(self, uuid, context, astronomer, folderpath):
        self.observations_folders = []
        self.calibrations_folders = []
        self.uuid = uuid
        super().__init__(context, astronomer, folderpath, '')

    def walk_telescope_folder(self):
        known_folderpaths = [o.folderpath for o in self.observations_folders] + \
                            [o.folderpath for o in self.calibrations_folders]

        for name, path in self._walk_folder():
            if not os.path.isdir(path):
                # If not a directory, skip it. Will skip __oort__.ini files too.
                continue
            if path in known_folderpaths:
                continue
            if name.lower().startswith('calib'):
                if self.context.debug: print(f' > Found a {self.prefix} {name} folder.')
                self.calibrations_folders.append(CalibrationsFolder(self.context, self.astronomer, path, name))
            else:
                # Prefix Observation and Datasets names with target name.
                if self.context.debug: print(f' > Found a {self.prefix} {name} folder.')
                self.observations_folders.append(FiltersFolder(self.context, self.astronomer, path, f'[{name}]'))

        for calibrations_folder in self.calibrations_folders:
            calibrations_folder.walk()
        for observations_folder in self.observations_folders:
            observations_folder.walk()

    @property
    def telescope_key(self):
        return f'telescope_{self.uuid}'

    def read_remote_telescope(self):
        if self.context.verbose: print(f'Reading remote telescope with uuid {self.uuid}')
        telescopes_api = Arcsecond.build_telescopes_api(**self.api_kwargs)
        response_detail, error = telescopes_api.read(self.uuid)
        if response_detail:
            response_detail['folder_name'] = self.name
            if self.astronomer:
                response_detail['astronomer'] = self.astronomer[0]
            else:
                response_detail['astronomer'] = ''
            self.context.telescopes.append(response_detail)
        else:
            msg = f'Unknown telescope with UUID {self.uuid}: {str(error)}'
            self.context.messages['warning'] = msg

    def uploads_calibrations_folders(self):
        for calibrations_folder in self.calibrations_folders:
            yield from calibrations_folder.upload(self.telescope_key)

    def uploads_observations_folders(self):
        for observations_folder in self.observations_folders:
            yield from observations_folder.upload_filters(self.telescope_key, 'observations')
