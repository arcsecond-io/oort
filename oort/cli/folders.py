import os
from typing import Optional, Union

import click
from arcsecond import ArcsecondAPI
from click import UUID
from peewee import DoesNotExist

from oort.server.errors import (InvalidOrgMembershipOortCloudError, InvalidOrganisationTelescopeOortCloudError,
                                NotLoggedInOortCloudError, UnknownOrganisationOortCloudError,
                                UnknownTelescopeOortCloudError)
from oort.shared.identity import Identity
from oort.shared.models import Organisation


def check_organisation(org_subdomain: str, debug: bool):
    try:
        Organisation.get(subdomain=org_subdomain)
    except DoesNotExist:
        org_resource, error = ArcsecondAPI.organisations(debug=debug).read(org_subdomain)
        if error:
            raise UnknownOrganisationOortCloudError(org_subdomain, str(error))
        else:
            Organisation.smart_create(subdomain=org_subdomain)


def check_organisation_telescope(org_subdomain: Optional[str],
                                 telescope_uuid: Optional[Union[str, UUID]],
                                 debug: bool) -> Optional[dict]:
    if not ArcsecondAPI.is_logged_in():
        raise NotLoggedInOortCloudError()

    telescope_detail = None

    if org_subdomain and not telescope_uuid:
        click.echo("Error: if an organisation is provided, you must specify a telescope UUID.")
        click.echo(f"Here a list of existing telescopes for organisation {org_subdomain}:")
        telescope_list, error = ArcsecondAPI.telescopes(debug=debug, organisation=org_subdomain).list()
        for telescope in telescope_list:
            click.echo(f" • {telescope['name']} ({telescope['uuid']})")

    elif org_subdomain and telescope_uuid:
        click.echo("Fetching telescope details...")
        telescope_uuid = str(telescope_uuid)
        telescope_detail, error = ArcsecondAPI.telescopes(debug=debug, organisation=org_subdomain).read(telescope_uuid)
        if error:
            raise InvalidOrganisationTelescopeOortCloudError(str(error))

    elif not org_subdomain and telescope_uuid:
        telescope_uuid = str(telescope_uuid)
        telescope_detail, error = ArcsecondAPI.telescopes(debug=debug).read(telescope_uuid)
        if error:
            raise UnknownTelescopeOortCloudError(str(error))

    if telescope_detail is not None and telescope_detail.get('coordinates', None) is None:
        site_uuid = telescope_detail.get('observing_site', None)
        site_detail, error = ArcsecondAPI.observingsites(debug=debug).read(site_uuid)
        telescope_detail['coordinates'] = site_detail.get('coordinates')

    return telescope_detail


def check_organisation_membership(org_subdomain: str, debug: bool) -> str:
    if org_subdomain is None or len(org_subdomain.strip()) == 0:
        return ''

    role = ArcsecondAPI.memberships(debug=debug).get(org_subdomain, None) if org_subdomain else None
    if org_subdomain and role is None:
        raise InvalidOrgMembershipOortCloudError(org_subdomain)

    return role


def save_upload_folders(folders: list,
                        org_subdomain: Optional[str],
                        org_role: Optional[str],
                        telescope_details: Optional[dict],
                        debug: bool) -> list:
    prepared_folders = []
    for raw_folder in folders:
        upload_folder = os.path.expanduser(os.path.realpath(raw_folder))
        if not os.path.exists(upload_folder):
            continue
        if os.path.isfile(upload_folder):
            upload_folder = os.path.dirname(upload_folder)

        telescope_uuid = ''
        longitude = None
        if telescope_details:
            telescope_uuid = telescope_details.get('uuid') or ''
            longitude = telescope_details.get('coordinates').get('longitude') or ''

        identity = Identity(username=ArcsecondAPI.username(debug=debug),
                            api_key=ArcsecondAPI.api_key(debug=debug),
                            subdomain=org_subdomain or '',
                            role=org_role or '',
                            telescope=telescope_uuid,
                            longitude=longitude,
                            debug=debug)

        identity.save_with_folder(upload_folder=upload_folder)
        prepared_folders.append((upload_folder, identity))

    return prepared_folders
