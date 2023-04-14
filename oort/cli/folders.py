import os
import pathlib
from typing import Optional, Union

import click
from arcsecond import ArcsecondAPI
from click import UUID
from peewee import DoesNotExist

from oort.server.errors import (InvalidAstronomerOortCloudError, InvalidOrgMembershipOortCloudError,
                                InvalidOrganisationTelescopeOortCloudError, InvalidOrganisationUploadKeyOortCloudError,
                                InvalidTelescopeOortCloudError, InvalidWatchOptionsOortCloudError,
                                UnknownOrganisationOortCloudError)
from oort.shared.config import get_oort_logger
from oort.shared.identity import Identity
from oort.shared.models import Organisation


def check_local_astronomer(api: str):
    test = os.environ.get('OORT_TESTS') == '1'

    username = ArcsecondAPI.username(test=test, api=api)
    if username is None:
        raise InvalidAstronomerOortCloudError('')

    upload_key = ArcsecondAPI.upload_key(test=test, api=api)
    return username, upload_key


def check_remote_organisation(org_subdomain: str, api: str = 'main'):
    try:
        return Organisation.get(subdomain=org_subdomain)
    except DoesNotExist:
        test = os.environ.get('OORT_TESTS') == '1'
        upload_key = ArcsecondAPI.upload_key(api=api)
        org_resource, error = ArcsecondAPI.organisations(test=test, api=api, upload_key=upload_key).read(org_subdomain)
        if error is not None:
            raise UnknownOrganisationOortCloudError(org_subdomain, str(error))
        else:
            return Organisation.create(subdomain=org_subdomain)


def check_local_astronomer_remote_organisation_membership(org_subdomain: str, api: str) -> str:
    test = os.environ.get('OORT_TESTS') == '1'
    upload_key = ArcsecondAPI.upload_key(api=api)

    # Reading local memberships if an org_subdomain is provided.
    memberships = ArcsecondAPI.memberships(test=test, api=api, upload_key=upload_key) if org_subdomain else None

    # An org_subdomain is provided, but memberships are empty.
    if org_subdomain and memberships in [None, {}]:
        raise InvalidOrgMembershipOortCloudError(org_subdomain)

    # Ok, an org_subdomain is provided and memberships are not empty. Checking for membership
    # of that org_subdomain AND checking it is at least a member (not a visitor).
    role = memberships.get(org_subdomain, None)
    if not role or role not in ['member', 'admin', 'superadmin']:
        raise InvalidOrgMembershipOortCloudError(org_subdomain)

    return role


def list_organisation_telescopes(org_subdomain: str, api: str):
    click.echo("Error: if an organisation is provided, you must specify a telescope UUID.")
    click.echo(f"Here is a list of existing telescopes for organisation {org_subdomain}:")

    test = os.environ.get('OORT_TESTS') == '1'
    upload_key = ArcsecondAPI.upload_key(api=api)
    telescope_list, error = ArcsecondAPI.telescopes(organisation=org_subdomain,
                                                    api=api,
                                                    test=test,
                                                    upload_key=upload_key).list()
    for telescope in telescope_list:
        click.echo(f" • {telescope['name']} ({telescope['uuid']})")


# The organisation is actually optional. It allows to check for a telescope
# also in the case of a custom astronomer.
def check_telescope(telescope_uuid: Union[str, UUID],
                    org_subdomain: Optional[str],
                    api: Optional[str]) -> \
        Optional[dict]:
    click.echo(" • Fetching telescope details...")

    test = os.environ.get('OORT_TESTS') == '1'
    upload_key = ArcsecondAPI.upload_key(api=api)

    kwargs = {'test': test, 'api': api, 'upload_key': upload_key}
    if org_subdomain:
        kwargs.update(organisation=org_subdomain)

    telescope_detail, error = ArcsecondAPI.telescopes(**kwargs).read(str(telescope_uuid))
    if error is not None:
        if org_subdomain:
            raise InvalidOrganisationTelescopeOortCloudError(str(telescope_uuid), org_subdomain, str(error))
        else:
            raise InvalidTelescopeOortCloudError(str(telescope_uuid), str(error))

    if telescope_detail is not None and telescope_detail.get('coordinates', None) is None:
        site_uuid = telescope_detail.get('observing_site', None)
        site_detail, error = ArcsecondAPI.observingsites(api=api, upload_key=upload_key).read(site_uuid)
        if site_detail:
            telescope_detail['coordinates'] = site_detail.get('coordinates')

    return telescope_detail


def check_remote_astronomer(username: str, upload_key: str, api: str):
    click.echo("Checking astronomer credentials...")

    if username is None or upload_key is None:
        raise InvalidWatchOptionsOortCloudError()

    test = os.environ.get('OORT_TESTS') == '1'
    upload_key = ArcsecondAPI.upload_key(api=api)

    result, error = ArcsecondAPI.me(test=test, api=api, upload_key=upload_key).read(username)
    if error is not None:
        raise InvalidAstronomerOortCloudError(username, upload_key, error_string=str(error))


def check_organisation_shared_keys(org_subdomain: str, username: str, upload_key: str, api: str):
    test = os.environ.get('OORT_TESTS') == '1'
    upload_key = ArcsecondAPI.upload_key(api=api)

    kwargs = {'api': api, 'test': test, 'organisation': org_subdomain, upload_key: upload_key}
    upload_keys_details, error = ArcsecondAPI.uploadkeys(**kwargs).list()
    if error is not None:
        InvalidWatchOptionsOortCloudError(str(error))

    upload_keys_mapping = {uk['username']: uk for uk in upload_keys_details}
    upload_key_details = upload_keys_mapping.get(username, None)
    if upload_key_details is None:
        raise InvalidOrganisationUploadKeyOortCloudError(org_subdomain, username, upload_key)

    upload_key = upload_key_details.get('key', None)
    if upload_key is None or upload_key != upload_key:
        raise InvalidOrganisationUploadKeyOortCloudError(org_subdomain, username, upload_key)


def parse_upload_watch_options(organisation: str = '',
                               telescope: str = '',
                               zip: bool = True,
                               api: str = 'main') -> Identity:
    assert api != ''
    telescope_uuid = telescope or ''
    org_subdomain = organisation or ''

    # Validation of the organisation #

    org = None
    org_role = ''
    if org_subdomain:
        # Check that the provided subdomain corresponds to an existing remote organisation.
        org = check_remote_organisation(org_subdomain, api)
        # Check that the provided subdomain is an organisation of which the current logged in astronomer is a member.
        org_role = check_local_astronomer_remote_organisation_membership(org_subdomain, api)

    # Validation of the telescope #

    # In every case, check for telescope details if a UUID is provided.
    telescope_details = None
    if telescope_uuid:
        telescope_details = check_telescope(telescope_uuid, org_subdomain, api)

    # Validation of the uploader #

    # Fetch the username of the currently logged in astronomer.
    username, upload_key = check_local_astronomer(api)
    if not username or not upload_key:
        raise InvalidWatchOptionsOortCloudError('Missing username or upload_key.')

    # If we have an organisation and no telescope UUID, we list the one available
    # and then raise an error
    if org is not None and telescope_details is None:
        list_organisation_telescopes(org_subdomain, api)
        raise InvalidWatchOptionsOortCloudError('For an organisation, a telescope UUID must be provided.')

    identity = Identity(username,
                        upload_key,
                        org_subdomain,
                        org_role,
                        telescope_uuid,
                        zip,
                        api)

    if telescope_details is not None:
        identity.attach_telescope_details(**telescope_details)

    return identity


def save_upload_folders(folders: list, identity: Identity) -> list:
    logger = get_oort_logger('cli', debug=identity.api == 'dev')

    prepared_folders = []
    for raw_folder in folders:
        upload_path = pathlib.Path(raw_folder).resolve()

        if not upload_path.exists() and os.environ.get('OORT_TESTS') != '1':
            logger.warn(f'Upload folder "{upload_path}" does not exists. Skipping.')
            continue

        if upload_path.is_file():
            upload_path = upload_path.parent

        identity.save_with_folder(upload_folder_path=str(upload_path))
        prepared_folders.append((str(upload_path), identity))

    return prepared_folders
