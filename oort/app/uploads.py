from .helpers import State, RootFolder

MAX_SIMULTANEOUS_UPLOADS = 3


class UploadsLocalState(State):
    def __init__(self, config):
        super().__init__(config)
        self.context.payload_group_update('state', **self.context.to_dict())
        self.context.payload_group_update('state', showTables=False)
        self.context.payload_update(current_uploads=[], finished_uploads=[])
        self.root_folder = RootFolder(self.context)

    def sync_telescopes(self):
        if not self.context.can_upload:
            return self.get_yield_string()

        self.root_folder.find_telescope_folders()
        self.root_folder.read_remote_telescopes()
        self.root_folder.walk_telescope_folders()

        return self.context.get_yield_string()

    def sync_calibrations_uploads(self):
        if not self.context.can_upload:
            return self.get_yield_string()

        self.context.payload_group_update('state', showTables=True)
        self.root_folder.upload_telescopes_calibrations()

        return self.context.get_yield_string()

    def sync_observations_uploads(self):
        if not self.context.can_upload:
            return self.get_yield_string()

        self.context.payload_group_update('state', showTables=True)
        self.root_folder.upload_telescopes_observations()

        return self.context.get_yield_string()
