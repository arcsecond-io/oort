import os
from configparser import ConfigParser

from arcsecond import Arcsecond

from .filewalkers import FilesWalker
from .telescopes import TelescopeFolder
from .utils import find


class RootFolder(FilesWalker):
    # Either a folder of multiple telescopes folders, or itself a telescope folder.

    def __init__(self, context, skip_root_files=True):
        super().__init__(context, context.folder)
        self.skip_root_files = skip_root_files

    def reset(self):
        self.other_folders = []
        self.telescope_folders = []

    def walk(self):
        self.reset()
        for name, path in self._walk_folder():
            # If it's a folder, check if it is a telescope one.
            if os.path.isdir(path):
                tel_uuid = self._look_for_telescope_uuid(path)
                if tel_uuid:
                    if self.context.debug: print(f'Found a Telescope folder: {name}')
                    self.telescope_folders.append(TelescopeFolder(tel_uuid, self.context, path))
                # else:
                #     self.other_folders.append(FilesWalker(self.context, path))
            else:
                # These are files. Check if we are inside a Telescope folder already.
                if name == '__oort__':
                    parent_path = os.path.dirname(path)
                    tel_uuid = self._look_for_telescope_uuid(parent_path)
                    if tel_uuid:
                        if self.context.debug: print(f'Found a Telescope folder: {name}')
                        self.telescope_folders.append(TelescopeFolder(tel_uuid, self.context, parent_path))
                    else:
                        # Don't know what to do here. Skip for now.
                        pass
                # else:
                # No, look for root files, if we are authorized to do so.
                # if self.skip_root_files is False:
                #     raise AttributeError('One needs to support root datasets in night logs for that.')
                # self.files.append(path)

    def _look_for_telescope_uuid(self, path):
        oort_filepath = os.path.join(path, '__oort__')
        if os.path.exists(oort_filepath) and os.path.isfile(oort_filepath):
            # Below will fail if the info is missing / wrong.
            with open(oort_filepath, 'r') as f:
                _config = ConfigParser()
                _config.read(oort_filepath)
                return _config['telescope']['uuid']

        return None

    def walk_telescope_folders(self):
        for telescope_folder in self.telescope_folders:
            telescope_folder.walk()

    def sync_telescopes(self):
        self.context.payload_group_update('messages', warning='')
        self.context.payload_update(telescopes=[])

        telescopes_api = Arcsecond.build_telescopes_api(debug=self.context.debug,
                                                        organisation=self.context.organisation)

        for telescope_folder in self.telescope_folders:
            telescope = self.fetch_resource('Telescope', telescopes_api, telescope_folder.uuid)
            if telescope:
                self.context.payload_append(telescopes=telescope)

        if len(self.context.get_payload('telescopes')) == 0:
            msg = 'No telescopes detected. Make sure this folder or sub-ones contain a file named __oort__ with a telescope UUID and relaunch command.'
            self.context.payload_group_update('messages', warning=msg)

    def sync_night_logs(self):
        self.context.payload_group_update('messages', warning='')
        self.context.payload_update(night_logs=[])

        logs_api = Arcsecond.build_nightlogs_api(debug=self.context.debug,
                                                 organisation=self.context.organisation)

        for telescope in self.context.get_payload('telescopes'):
            new_log = self.sync_resource('Night Log',
                                         logs_api,
                                         date=self.context.current_date,
                                         telescope=telescope['uuid'])

            if new_log:
                self.context.payload_append(night_logs=new_log)

    def sync_telescopes_calibrations(self):
        night_logs = self.context.get_payload('night_logs')
        for telescope_folder in self.telescope_folders:
            night_log = find(night_logs, telescope=telescope_folder.uuid)
            if night_log is None:
                continue
            telescope_folder.sync_calibrations_folders(night_log=night_log['uuid'])

    def sync_telescopes_observations(self):
        night_logs = self.context.get_payload('night_logs')
        for telescope_folder in self.telescope_folders:
            night_log = find(night_logs, telescope=telescope_folder.uuid)
            if night_log is None:
                continue
            telescope_folder.sync_observations_folders(night_log=night_log['uuid'])

    def upload_telescopes_calibrations(self):
        for telescope_folder in self.telescope_folders:
            telescope_folder.uploads_calibrations_folders()

    def upload_telescopes_observations(self):
        for telescope_folder in self.telescope_folders:
            telescope_folder.uploads_observations_folders()
