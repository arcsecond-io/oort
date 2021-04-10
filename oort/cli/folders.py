import os
from typing import Optional, Union

import click
from arcsecond import ArcsecondAPI
from click import UUID
from peewee import DoesNotExist

from oort.server.errors import (InvalidAstronomerOortCloudError, InvalidOrgMembershipOortCloudError,
                                InvalidOrganisationTelescopeOortCloudError,
                                InvalidOrganisationUploadKeyOortCloudError, InvalidWatchOptionsOortCloudError,
                                UnknownOrganisationOortCloudError)
from oort.shared.config import get_logger
from oort.shared.identity import Identity
from oort.shared.models import Organisation


def check_local_astronomer(debug: bool):
    test = os.environ.get('OORT_TESTS') == '1'
    username = ArcsecondAPI.username(debug=debug, test=test)
    if username is None:
        raise InvalidAstronomerOortCloudError('')
    api_key = ArcsecondAPI.api_key(debug=debug, test=test)
    return username, api_key


def check_remote_organisation(org_subdomain: str, debug: bool):
    try:
        return Organisation.get(subdomain=org_subdomain)
    except DoesNotExist:
        test = os.environ.get('OORT_TESTS') == '1'
        org_resource, error = ArcsecondAPI.organisations(debug=debug, test=test).read(org_subdomain)
        if error:
            raise UnknownOrganisationOortCloudError(org_subdomain, str(error))
        else:
            return Organisation.smart_create(subdomain=org_subdomain)


def check_local_astronomer_remote_organisation_membership(org_subdomain: str, debug: bool) -> str:
    test = os.environ.get('OORT_TESTS') == '1'
    memberships = ArcsecondAPI.memberships(debug=debug, test=test) if org_subdomain else None
    if org_subdomain and memberships in [None, {}]:
        raise InvalidOrgMembershipOortCloudError(org_subdomain)

    role = memberships.get(org_subdomain, None)
    if not role or role not in ['member', 'admin', 'superadmin']:
        raise InvalidOrgMembershipOortCloudError(org_subdomain)

    return role


def list_organisation_telescopes(org_subdomain: str, debug: bool):
    click.echo("Error: if an organisation is provided, you must specify a telescope UUID.")
    click.echo(f"Here is a list of existing telescopes for organisation {org_subdomain}:")

    test = os.environ.get('OORT_TESTS') == '1'
    telescope_list, error = ArcsecondAPI.telescopes(debug=debug, test=test, organisation=org_subdomain).list()
    for telescope in telescope_list:
        click.echo(f" • {telescope['name']} ({telescope['uuid']})")


# The organisation is actually optional. It allows to check for a telescope
# also in the case of a custom astronomer.
def check_organisation_telescope(telescope_uuid: Optional[Union[str, UUID]],
                                 org_subdomain: Optional[str],
                                 debug: bool) -> Optional[dict]:
    click.echo("Fetching telescope details...")

    test = os.environ.get('OORT_TESTS') == '1'
    kwargs = {'debug': debug, 'test': test}
    if org_subdomain:
        kwargs.update(organisation=org_subdomain)

    telescope_detail, error = ArcsecondAPI.telescopes(**kwargs).read(str(telescope_uuid))
    if error:
        raise InvalidOrganisationTelescopeOortCloudError(str(error))

    if telescope_detail is not None and telescope_detail.get('coordinates', None) is None:
        site_uuid = telescope_detail.get('observing_site', None)
        site_detail, error = ArcsecondAPI.observingsites(debug=debug).read(site_uuid)
        if site_detail:
            telescope_detail['coordinates'] = site_detail.get('coordinates')

    return telescope_detail


def check_remote_astronomer(username: str, api_key: str, debug: bool):
    click.echo("Checking astronomer credentials...")

    if username is None or api_key is None:
        raise InvalidWatchOptionsOortCloudError()

    test = os.environ.get('OORT_TESTS') == '1'
    result, error = ArcsecondAPI.me(debug=debug, test=test).read(username)
    if error:
        raise InvalidAstronomerOortCloudError(username, api_key)


def check_organisation_uploadkeys(org_subdomain: str, username: str, api_key: str, debug: bool):
    test = os.environ.get('OORT_TESTS') == '1'
    kwargs = {'debug': debug, 'test': test, 'organisation': org_subdomain}
    upload_keys_details, error = ArcsecondAPI.uploadkeys(**kwargs).list()
    if error:
        InvalidWatchOptionsOortCloudError(str(error))

    upload_keys_mapping = {uk['username']: uk for uk in upload_keys_details}
    upload_key_details = upload_keys_mapping.get(username, None)
    if upload_key_details is None:
        raise InvalidOrganisationUploadKeyOortCloudError(org_subdomain, username, api_key)

    upload_key = upload_key_details.get('key', None)
    if upload_key is None or upload_key != api_key:
        raise InvalidOrganisationUploadKeyOortCloudError(org_subdomain, username, api_key)


def parse_upload_watch_options(o: Optional[str] = None,
                               organisation: Optional[str] = None,
                               t: Optional[str] = None,
                               telescope: Optional[str] = None,
                               astronomer: Union[Optional[str], Optional[str]] = (None, None),
                               debug: Optional[bool] = False):
    telescope_uuid = t or telescope or ''
    org_subdomain = o or organisation or ''

    ### Validation of the organisation ###

    org = None
    org_role = ''
    if org_subdomain:
        # Check that the provided subdomain corresponds to an existing remote organisation.
        org = check_remote_organisation(org_subdomain, debug)
        # Check that the provided subdomain is an organisation of which the current logged in astronomer is a member.
        org_role = check_local_astronomer_remote_organisation_membership(org_subdomain, debug)

    ### Validation of the telescope ###

    # In every case, check for telescope details if a UUID is provided.
    telescope_details = None
    if telescope_uuid:
        telescope_details = check_organisation_telescope(telescope_uuid, org_subdomain, debug)

    ### Validation of the uploader ###

    username = ''
    api_key = ''

    # No custom astronomer for uploading. If no org, fine. If an org, one need the telescope.
    if astronomer == (None, None):
        # Fetch the username of the currently logged in astronomer.
        username, api_key = check_local_astronomer(debug)
        if not username or not api_key:
            raise InvalidWatchOptionsOortCloudError('Missing username or api_key.')

        # If we have an organisation and no telescope UUID, we list the one available
        # and then raise an error
        if org is not None and telescope_details is None:
            list_organisation_telescopes(org_subdomain, debug)
            raise InvalidWatchOptionsOortCloudError('For an organisation, a telescope UUID must be provided.')

    # We have a custom astronomer. Check that the organisation is allowed to upload on behalf of it.
    else:
        username, api_key = astronomer
        # Make sure the remote astronomer actually exists.
        check_remote_astronomer(username, api_key, debug)

        if org is None:
            raise InvalidWatchOptionsOortCloudError('')

        # Check that the custom astronomer has a valid upload_key for the given organisation.
        # This is where the knot is. This check can only be made by a member of the registered organisation.
        check_organisation_uploadkeys(org_subdomain, username, api_key, debug)

    return username, api_key, org_subdomain, org_role, telescope_details


def save_upload_folders(folders: list,
                        username: Optional[str],
                        api_key: Optional[str],
                        org_subdomain: Optional[str],
                        org_role: Optional[str],
                        telescope_details: Optional[dict],
                        debug: bool) -> list:
    logger = get_logger(debug=debug)
    prepared_folders = []
    for raw_folder in folders:
        upload_folder = os.path.expanduser(os.path.realpath(raw_folder))
        if not os.path.exists(upload_folder) and os.environ.get('OORT_TESTS') != '1':
            logger.warn(f'Upload folder "{upload_folder}" does not exists. Skipping.')
            continue
        if os.path.isfile(upload_folder):
            upload_folder = os.path.dirname(upload_folder)

        telescope_uuid = ''
        longitude = None
        if telescope_details:
            telescope_uuid = telescope_details.get('uuid') or ''
            longitude = telescope_details.get('coordinates').get('longitude') or ''

        identity = Identity(username=username,
                            api_key=api_key or '',
                            subdomain=org_subdomain or '',
                            role=org_role or '',
                            telescope=telescope_uuid,
                            longitude=longitude,
                            debug=debug)

        identity.save_with_folder(upload_folder_path=upload_folder)
        prepared_folders.append((upload_folder, identity))

    return prepared_folders
