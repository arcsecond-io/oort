from .helpers import Context, RootFolder

MAX_SIMULTANEOUS_UPLOADS = 3


class UploadsLocalState:
    def __init__(self, config):
        self.context = Context(config)
        self.context.state['showTables'] = False
        self.root_folder = RootFolder(self.context)

    def sync_telescopes(self):
        if self.context.verbose:
            print('Syncing telescopes...')

        if self.context.can_upload:
            self.root_folder.find_telescope_folders()
            self.root_folder.read_remote_telescopes()
            self.root_folder.walk_telescope_folders()

        return self.context.get_yield_string()

    def sync_calibrations_uploads(self):
        if self.context.verbose:
            print('Syncing calibrations uploads...')

        if self.context.can_upload:
            self.context.state['showTables'] = True
            self.root_folder.upload_telescopes_calibrations_folders()

        return self.context.get_yield_string()

    def sync_observations_uploads(self):
        if self.context.verbose:
            print('Syncing observations uploads...')

        if self.context.can_upload:
            self.context.state['showTables'] = True
            self.root_folder.upload_telescopes_observations_folders()

        return self.context.get_yield_string()
