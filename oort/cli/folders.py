import os
from typing import Optional, Union

import click
from arcsecond import ArcsecondAPI
from click import UUID
from peewee import DoesNotExist

from oort.server.errors import (InvalidAstronomerOortCloudError, InvalidOrgMembershipOortCloudError,
                                InvalidOrganisationTelescopeOortCloudError,
                                UnknownOrganisationOortCloudError)
from oort.shared.identity import Identity
from oort.shared.models import Organisation
from oort.shared.utils import find_first_in_list


def check_username(debug: bool):
    test = os.environ.get('OORT_TESTS') == '1'
    return ArcsecondAPI.username(debug=debug, test=test)


def check_organisation(org_subdomain: str, debug: bool):
    try:
        Organisation.get(subdomain=org_subdomain)
    except DoesNotExist:
        test = os.environ.get('OORT_TESTS') == '1'
        org_resource, error = ArcsecondAPI.organisations(debug=debug, test=test).read(org_subdomain)
        if error:
            raise UnknownOrganisationOortCloudError(org_subdomain, str(error))
        else:
            Organisation.smart_create(subdomain=org_subdomain)


def check_organisation_local_membership(org_subdomain: str, debug: bool) -> str:
    if org_subdomain is None or len(org_subdomain.strip()) == 0:
        return ''

    test = os.environ.get('OORT_TESTS') == '1'
    role = ArcsecondAPI.memberships(debug=debug, test=test).get(org_subdomain, None) if org_subdomain else None
    if org_subdomain and role is None:
        raise InvalidOrgMembershipOortCloudError(org_subdomain)

    return role


def list_organisation_telescopes(org_subdomain: str, debug: bool):
    click.echo("Error: if an organisation is provided, you must specify a telescope UUID.")
    click.echo(f"Here is a list of existing telescopes for organisation {org_subdomain}:")

    test = os.environ.get('OORT_TESTS') == '1'
    telescope_list, error = ArcsecondAPI.telescopes(debug=debug, test=test, organisation=org_subdomain).list()
    for telescope in telescope_list:
        click.echo(f" • {telescope['name']} ({telescope['uuid']})")


def check_organisation_telescope(telescope_uuid: Optional[Union[str, UUID]],
                                 org_subdomain: Optional[str],
                                 api_key: Optional[str],
                                 debug: bool) -> Optional[dict]:
    click.echo("Fetching telescope details...")

    test = os.environ.get('OORT_TESTS') == '1'
    kwargs = {'debug': debug, 'test': test}
    if org_subdomain:
        kwargs.update(organisation=org_subdomain)
    if api_key:
        kwargs.update(api_key=api_key)

    telescope_detail, error = ArcsecondAPI.telescopes(**kwargs).read(str(telescope_uuid))
    if error:
        raise InvalidOrganisationTelescopeOortCloudError(str(error))

    if telescope_detail is not None and telescope_detail.get('coordinates', None) is None:
        site_uuid = telescope_detail.get('observing_site', None)
        site_detail, error = ArcsecondAPI.observingsites(debug=debug).read(site_uuid)
        if site_detail:
            telescope_detail['coordinates'] = site_detail.get('coordinates')

    return telescope_detail


def check_astronomer_credentials(username: str, api_key: str, debug: bool):
    click.echo("Checking astronomer credentials...")

    test = os.environ.get('OORT_TESTS') == '1'
    result, error = ArcsecondAPI.me(debug=debug, test=test, api_key=api_key).read(username)
    if error:
        raise InvalidAstronomerOortCloudError(username, api_key)


def check_astronomer_org_membership(org_subdomain: str, username: str, api_key: str, debug: bool):
    click.echo("Checking astronomer membership...")

    test = os.environ.get('OORT_TESTS') == '1'
    result, error = ArcsecondAPI.members(organisation=org_subdomain, debug=debug, test=test, api_key=api_key).list()

    if error:
        raise InvalidOrgMembershipOortCloudError(org_subdomain)

    if not find_first_in_list(result, username=username):
        raise InvalidOrgMembershipOortCloudError(org_subdomain)

    membership = find_first_in_list(result, username=username)
    if membership.get('role') not in ['member', 'admin', 'superadmin']:
        raise InvalidOrgMembershipOortCloudError(org_subdomain)


def save_upload_folders(folders: list,
                        username: Optional[str],
                        api_key: Optional[str],
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

        identity = Identity(username=username or ArcsecondAPI.username(debug=debug),
                            api_key=api_key or ArcsecondAPI.api_key(debug=debug),
                            subdomain=org_subdomain or '',
                            role=org_role or '',
                            telescope=telescope_uuid,
                            longitude=longitude,
                            debug=debug)

        identity.save_with_folder(upload_folder=upload_folder)
        prepared_folders.append((upload_folder, identity))

    return prepared_folders
