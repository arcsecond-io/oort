import os
from configparser import ConfigParser

from arcsecond import ArcsecondConnectionError

from .filewalker import FilesWalker
from .telescopes import TelescopeFolder


class RootFolder(FilesWalker):
    def __init__(self, context):
        super().__init__(context, None, context.folder)

    def reset(self):
        self.other_folders = []
        self.telescope_folders = []

    def find_telescope_folders(self):
        self.reset()
        for name, path in self._walk_folder():
            # If it's a folder, check if it is a telescope one.
            if os.path.isdir(path):
                tel_uuid = self._look_for_telescope_uuid(path)
                if tel_uuid:
                    if self.context.debug: print(f'Found a Telescope folder: {name}')
                    astronomer = self._look_for_astronomer(path)
                    if astronomer and self.context.debug: print(f'For astronomer: {astronomer[0]}')
                    self.telescope_folders.append(TelescopeFolder(tel_uuid, self.context, astronomer, path))
                # else:
                #     self.other_folders.append(FilesWalker(self.context, path))
            else:
                # These are files. Check if we are inside a Telescope folder already.
                if name == '__oort__':
                    parent_path = os.path.dirname(path)
                    tel_uuid = self._look_for_telescope_uuid(parent_path)
                    if tel_uuid:
                        if self.context.debug: print(f'Found a Telescope folder: {name}')
                        astronomer = self._look_for_astronomer(parent_path)
                        if astronomer and self.context.debug: print(f'For astronomer: {astronomer[0]}')
                        self.telescope_folders.append(TelescopeFolder(tel_uuid, self.context, astronomer, parent_path))
                    # else:
                    #     # Don't know what to do here. Skip for now.
                    #     pass
                # else:
                # No, look for root files, if we are authorized to do so.
                # if self.skip_root_files is False:
                #     raise AttributeError('One needs to support root datasets in night logs for that.')
                # self.files.append(path)

    def _get_oort_config(self, path):
        _config = None
        oort_filepath = os.path.join(path, '__oort__')
        if os.path.exists(oort_filepath) and os.path.isfile(oort_filepath):
            # Below will fail if the info is missing / wrong.
            _config = ConfigParser()
            with open(oort_filepath, 'r') as f:
                _config.read(oort_filepath)
        return _config

    def _look_for_telescope_uuid(self, path):
        _config = self._get_oort_config(path)
        if _config and 'telescope' in _config:
            return _config['telescope']['uuid']
        return None

    def _look_for_astronomer(self, path):
        _config = self._get_oort_config(path)
        if _config and 'astronomer' in _config:
            return (_config['astronomer']['username'], _config['astronomer']['api_key'])
        return None

    def walk_telescope_folders(self):
        for telescope_folder in self.telescope_folders:
            telescope_folder.walk()

    def read_remote_telescopes(self):
        self.context.payload_group_update('messages', warning='')
        self.context.payload_update(telescopes=[])

        try:
            for telescope_folder in self.telescope_folders:
                telescope_folder.read_remote_telescope()
        except ArcsecondConnectionError as error:
            self.context.payload_group_update('messages', warning=str(error))
        else:
            if len(self.context.get_payload('telescopes')) == 0 and self.context.get_group_payload('messages', 'warning') == '':
                msg = 'No telescopes detected. Make sure this folder or sub-ones contain a file named __oort__ '
                msg += 'with a telescope UUID and relaunch command.'
                self.context.payload_group_update('messages', warning=msg)

    def upload_telescopes_calibrations(self):
        for telescope_folder in self.telescope_folders:
            telescope_folder.uploads_calibrations_folders()

    def upload_telescopes_observations(self):
        for telescope_folder in self.telescope_folders:
            telescope_folder.uploads_observations_folders()
