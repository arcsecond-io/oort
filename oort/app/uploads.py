from .helpers import Context, RootFolder

MAX_SIMULTANEOUS_UPLOADS = 3


class UploadsLocalState:
    def __init__(self, config):
        self.context = Context(config)
        self.context.state['showTables'] = False
        self.root_folder = RootFolder(self.context)

    def sync_telescopes(self):
        if not self.context.can_upload:
            yield self.context.get_yield_string()
            return

        if self.context.verbose:
            print('Syncing telescopes...')

        self.root_folder.find_telescope_folders()
        self.root_folder.read_remote_telescopes()
        yield self.context.get_yield_string()

        for telescope_folder in self.root_folder.telescope_folders:
            telescope_folder.walk_telescope_folder()
            yield self.context.get_yield_string()

    def sync_calibrations_uploads(self):
        if not self.context.can_upload:
            yield self.context.get_yield_string()
            return

        if self.context.verbose:
            print('Syncing calibrations uploads...')

        self.context.state['showTables'] = True
        for telescope_folder in self.root_folder.telescope_folders:
            yield from telescope_folder.uploads_calibrations_folders()

    def sync_observations_uploads(self):
        if not self.context.can_upload:
            yield self.context.get_yield_string()
            return

        if self.context.verbose:
            print('Syncing observations uploads...')

        self.context.state['showTables'] = True
        for telescope_folder in self.root_folder.telescope_folders:
            yield from telescope_folder.uploads_observations_folders()
