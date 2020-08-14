import os

from arcsecond import Arcsecond

from oort.server.errors import (
    InvalidOrganisationTelescopeOortCloudError,
    NotLoggedInOortCloudError,
    UnknownTelescopeOortCloudError
)
from oort.shared.identity import Identity
from oort.shared.utils import look_for_telescope_uuid


def save_upload_folders(folders, telescope_uuid, debug):
    if not Arcsecond.is_logged_in():
        raise NotLoggedInOortCloudError()

    role, organisation, telescope_data = None, None, None

    if telescope_uuid is not None:
        # Checking whether telescope exists.
        api = Arcsecond.build_telescopes_api(debug=debug)
        telescope_data, error = api.read(telescope_uuid)
        if error:
            raise UnknownTelescopeOortCloudError(telescope_uuid)

    # Check whether telescope is part of current organisation
    # NOTE: Logged in with organisation necessarily imply uploading for that organisation.
    memberships = Arcsecond.memberships(debug=debug)
    if telescope_data and len(memberships) > 0:
        for org_subdomain, membership_role in memberships.items():
            org_api = Arcsecond.build_telescopes_api(debug=debug, organisation=org_subdomain)
            org_telescope_data, error = org_api.read(telescope_uuid)

            if error is None:
                organisation = org_subdomain
                role = membership_role
                break

        if organisation is None:
            raise InvalidOrganisationTelescopeOortCloudError('')

    prepared_folders = []
    for raw_folder in folders:
        upload_folder = os.path.expanduser(os.path.realpath(raw_folder))
        if not os.path.exists(upload_folder):
            continue
        if os.path.isfile(upload_folder):
            upload_folder = os.path.dirname(upload_folder)

        legacy_telescope_uuid = look_for_telescope_uuid(upload_folder)

        if telescope_uuid and legacy_telescope_uuid and telescope_uuid != legacy_telescope_uuid:
            raise InvalidOrganisationTelescopeOortCloudError(legacy_telescope_uuid)

        final_telescope_uuid = telescope_uuid or legacy_telescope_uuid

        identity = Identity(username=Arcsecond.username(debug=debug),
                            api_key=Arcsecond.api_key(debug=debug),
                            organisation=organisation or '',
                            role=role or '',
                            telescope=final_telescope_uuid or '',
                            debug=debug)

        identity.save_with_folder(upload_folder=upload_folder)
        prepared_folders.append((upload_folder, identity))

    return prepared_folders
