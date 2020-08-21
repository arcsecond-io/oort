import os

import click
from arcsecond import ArcsecondAPI

from oort.server.errors import (
    InvalidOrganisationTelescopeOortCloudError,
    NotLoggedInOortCloudError,
    UnknownTelescopeOortCloudError, InvalidOrgMembershipOortCloudError
)
from oort.shared.identity import Identity


def check_organisation_telescope(org_subdomain, telescope_uuid, debug):
    if not ArcsecondAPI.is_logged_in():
        raise NotLoggedInOortCloudError()

    telescope_detail = None

    if org_subdomain and not telescope_uuid:
        click.echo(f"Error: if an organisation is provided, you must specify a telescope UUID.")
        click.echo(f"Here a list of existing telescopes for organisation {org_subdomain}:")
        telescope_list, error = ArcsecondAPI.telescopes(debug=debug, organisation=org_subdomain).list()
        for telescope in telescope_list:
            click.echo(f" • {telescope['name']} : {telescope['uuid']}")

    elif org_subdomain and telescope_uuid:
        telescope_detail, error = ArcsecondAPI.telescopes(debug=debug, organisation=org_subdomain).read(telescope_uuid)
        if error:
            raise InvalidOrganisationTelescopeOortCloudError(str(error))

    elif not org_subdomain and telescope_uuid:
        telescope_detail, error = ArcsecondAPI.telescopes(debug=debug).read(telescope_uuid)
        if error:
            raise UnknownTelescopeOortCloudError(str(error))

    return telescope_detail


def check_organisation_membership(org_subdomain, debug):
    if org_subdomain is None or len(org_subdomain.strip()) == 0:
        return ''

    role = ArcsecondAPI.memberships(debug=debug).get(org_subdomain, None) if org_subdomain else None
    if org_subdomain and role is None:
        raise InvalidOrgMembershipOortCloudError(org_subdomain)

    return role


def save_upload_folders(folders, org_subdomain, org_role, telescope_uuid, debug):
    prepared_folders = []
    for raw_folder in folders:
        upload_folder = os.path.expanduser(os.path.realpath(raw_folder))
        if not os.path.exists(upload_folder):
            continue
        if os.path.isfile(upload_folder):
            upload_folder = os.path.dirname(upload_folder)

        # legacy_telescope_uuid = look_for_telescope_uuid(upload_folder)
        #
        # if telescope_uuid and legacy_telescope_uuid and telescope_uuid != legacy_telescope_uuid:
        #     raise InvalidOrganisationTelescopeOortCloudError(legacy_telescope_uuid)
        # final_telescope_uuid = telescope_uuid or legacy_telescope_uuid


        identity = Identity(username=ArcsecondAPI.username(debug=debug),
                            api_key=ArcsecondAPI.api_key(debug=debug),
                            organisation=org_subdomain or '',
                            role=org_role or '',
                            telescope=final_telescope_uuid or '',
                            debug=debug)

        identity.save_with_folder(upload_folder=upload_folder)
        prepared_folders.append((upload_folder, identity))

    return prepared_folders
