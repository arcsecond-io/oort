from arcsecond import Arcsecond

from .state import LocalState


class UploadsLocalState(LocalState):
    def __init__(self, config):
        super().__init__(config)
        self.update_payload('state', self.context.to_dict())
