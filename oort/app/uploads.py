from .helpers import State, RootFolder, FileWrapper, find

MAX_SIMULTANEOUS_UPLOADS = 3


class UploadsLocalState(State):
    def __init__(self, config):
        super().__init__(config)
        self.context.payload_group_update('state', **self.context.to_dict())
        self.context.payload_group_update('state', showTables=False)
        self.context.payload_update(current_uploads=[], finished_uploads=[])
        self.root = RootFolder(self.context)

    def sync_telescopes_and_night_logs(self):
        if not self.context.can_upload:
            return self.get_yield_string()

        self.root.walk()  # Only first depth level.
        self.root.sync_telescopes()
        self.root.sync_night_logs()

        return self.context.get_yield_string()

    def sync_observations_and_calibrations(self):
        if not self.context.can_upload:
            return self.get_yield_string()

        self.root.walk_telescope_folders()
        self.root.sync_telescopes_calibrations()
        self.root.sync_telescopes_observations()

        return self.context.get_yield_string()

    def sync_calibrations_uploads(self):
        if not self.context.can_upload:
            return self.get_yield_string()

        self.context.payload_group_update('state', showTables=True)
        self.root.upload_telescopes_calibrations()

        return self.context.get_yield_string()

    def sync_observations_uploads(self):
        if not self.context.can_upload:
            return self.get_yield_string()

        self.context.payload_group_update('state', showTables=True)
        self.root.upload_telescopes_observations()

        return self.context.get_yield_string()
