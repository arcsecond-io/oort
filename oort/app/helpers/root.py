import os
from configparser import ConfigParser

from arcsecond import ArcsecondConnectionError

from .constants import OORT_FILENAME
from .filesfolder import FilesFolder
from .telescopes import TelescopeFolder
from .utils import find_first_in_list


class RootFolder(FilesFolder):
    def __init__(self, context):
        self.other_folders = []
        self.telescope_folders = []
        super().__init__(context, None, context.folder)

    def find_telescope_folders(self):
        # Do not reset every time.
        for name, path in self._walk_folder():
            # If it's a folder, check if it is a telescope one.
            if os.path.isdir(path):
                self._look_for_telescope(path, name)
            else:
                # These are files. Check if we are inside a Telescope folder already.
                if name == OORT_FILENAME:
                    parent_path = os.path.dirname(path)
                    parent_name = os.path.dirname(parent_path)
                    self._look_for_telescope(parent_path, parent_name)

    def _look_for_telescope(self, path, name):
        known_uuids = [tel.uuid for tel in self.telescope_folders]
        tel_uuid = self._look_for_telescope_uuid(path)
        if tel_uuid and tel_uuid not in known_uuids:
            if self.context.debug or self.context.verbose:
                print(f'Found a Telescope folder: {name}')
            astronomer = self._look_for_astronomer(path)
            if astronomer and (self.context.debug or self.context.verbose):
                print(f'For astronomer: {astronomer[0]}')
            self.telescope_folders.append(TelescopeFolder(tel_uuid, self.context, astronomer, path))

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

    def _get_oort_config(self, path):
        _config = None
        oort_filepath = os.path.join(path, OORT_FILENAME)
        if os.path.exists(oort_filepath) and os.path.isfile(oort_filepath):
            # Below will fail if the info is missing / wrong.
            _config = ConfigParser()
            with open(oort_filepath, 'r') as f:
                _config.read(oort_filepath)
        return _config

    def read_remote_telescopes(self):
        self.context.messages['warning'] = ''

        try:
            for telescope_folder in self.telescope_folders:
                if find_first_in_list(self.context.telescopes, uuid=telescope_folder.uuid) is None:
                    telescope_folder.read_remote_telescope()
        except ArcsecondConnectionError as error:
            self.context.messages['warning'] = str(error)
            if self.context.debug or self.context.verbose: print(str(error))
        else:
            if self.context.debug or self.context.verbose:
                print(f'{len(self.context.telescopes)} telescopes synced.')
            if len(self.context.telescopes) == 0 and self.context.messages['warning'] == '':
                msg = f'No telescopes detected. Make sure this folder or sub-ones contain a file named {OORT_FILENAME} '
                msg += 'with a telescope UUID declared in a [telescope] section and relaunch command.'
                self.context.messages['warning'] = msg
                if self.context.debug or self.context.verbose: print(msg)
