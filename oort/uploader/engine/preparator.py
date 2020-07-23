from arcsecond import Arcsecond

from oort.shared.models import *
from .errors import *
from .identity import Identity
from .packer import UploadPack


class UploadPreparator(object):
    """Logic to determine dataset, night_log and observations/calibrations from filepath."""

    def __init__(self, pack: UploadPack, identity: Identity):
        self._pack = pack
        self._identity = identity

    def _check_telescope_existence(self):
        if not self._identity.telescope:
            pass

        if Telescope.exists(self._identity.telescope):
            return

        api = Arcsecond.build_telescopes_api(debug=self._identity.debug)
        telescope_data, error = api.read(self._identity.telescope)

        if error:
            raise UploadPreparationError(f'Unknown telescope with UUID {self._identity.telescope}.')

        if telescope_data:
            Telescope.create(uuid=telescope_data.get('uuid'), name=telescope_data.get('name'))

    def _check_telescope_in_organisation(self):
        if self._identity.organisation and not self._identity.telescope:
            msg = f'Missing telescope UUID to use for organisation {self._identity.organisation}.'
            raise UploadPreparationError(msg)

        try:
            org = Organisation.get(subdomain=self._identity.organisation)
        except DoesNotExist:
            org = Organisation.create(subdomain=self._identity.organisation)

        try:
            telescope = org.telescopes.get(uuid=self._identity.telescope)
        except DoesNotExist:
            # check remote apis
            pass

    def _check_user_in_organisation(self):
        pass

    def _check_night_log_existence(self):
        pass

    def _check_dataset_existence(self):
        pass

    def prepare(self):
        self._check_telescope_existence()
        self._check_telescope_in_organisation()
        self._check_user_in_organisation()
        self._check_night_log_existence()
        self._check_dataset_existence()
