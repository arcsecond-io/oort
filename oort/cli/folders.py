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


def check_local_astronomer(debug: bool, verbose: bool):
    test = os.environ.get('OORT_TESTS') == '1'

    username = ArcsecondAPI.username(debug=debug, test=test, verbose=verbose)
    if username is None:
        raise InvalidAstronomerOortCloudError('')

    upload_key = ArcsecondAPI.upload_key(debug=debug, test=test, verbose=verbose)
    return username, upload_key


def check_remote_organisation(org_subdomain: str, debug: bool, verbose: bool):
    try:
        return Organisation.get(subdomain=org_subdomain)
    except DoesNotExist:
        test = os.environ.get('OORT_TESTS') == '1'
        org_resource, error = ArcsecondAPI.organisations(debug=debug, test=test, verbose=verbose).read(org_subdomain)
        if error is not None:
            raise UnknownOrganisationOortCloudError(org_subdomain, str(error))
        else:
            return Organisation.create(subdomain=org_subdomain)


def check_local_astronomer_remote_organisation_membership(org_subdomain: str, debug: bool, verbose: bool) -> str:
    test = os.environ.get('OORT_TESTS') == '1'

    # Reading local memberships if a org_subdomain is provided.
    memberships = ArcsecondAPI.memberships(debug=debug, test=test, verbose=verbose) if org_subdomain else None

    # An org_subdomain is provided, but memberships are empty.
    if org_subdomain and memberships in [None, {}]:
        raise InvalidOrgMembershipOortCloudError(org_subdomain)

    # Ok, an org_subdomain is provided and memberships are not empty. Checking for membership
    # of that org_subdomain AND checking it is at least a member (not a visitor).
    role = memberships.get(org_subdomain, None)
    if not role or role not in ['member', 'admin', 'superadmin']:
        raise InvalidOrgMembershipOortCloudError(org_subdomain)

    return role


def list_organisation_telescopes(org_subdomain: str, debug: bool, verbose: bool):
    click.echo("Error: if an organisation is provided, you must specify a telescope UUID.")
    click.echo(f"Here is a list of existing telescopes for organisation {org_subdomain}:")

    test = os.environ.get('OORT_TESTS') == '1'
    telescope_list, error = ArcsecondAPI.telescopes(organisation=org_subdomain,
                                                    debug=debug,
                                                    test=test,
                                                    verbose=verbose).list()
    for telescope in telescope_list:
        click.echo(f" • {telescope['name']} ({telescope['uuid']})")


# The organisation is actually optional. It allows to check for a telescope
# also in the case of a custom astronomer.
def check_telescope(telescope_uuid: Optional[Union[str, UUID]],
                    org_subdomain: Optional[str],
                    debug: bool,
                    verbose: bool) -> Optional[dict]:
    click.echo(" • Fetching telescope details...")

    test = os.environ.get('OORT_TESTS') == '1'
    kwargs = {'debug': debug, 'test': test, 'verbose': verbose}
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
        site_detail, error = ArcsecondAPI.observingsites(debug=debug).read(site_uuid)
        if site_detail:
            telescope_detail['coordinates'] = site_detail.get('coordinates')

    return telescope_detail


def check_remote_astronomer(username: str, upload_key: str, debug: bool, verbose: bool):
    click.echo("Checking astronomer credentials...")

    if username is None or upload_key is None:
        raise InvalidWatchOptionsOortCloudError()

    test = os.environ.get('OORT_TESTS') == '1'
    result, error = ArcsecondAPI.me(debug=debug, test=test, verbose=verbose).read(username)
    if error is not None:
        raise InvalidAstronomerOortCloudError(username, upload_key, error_string=str(error))


def check_organisation_shared_keys(org_subdomain: str, username: str, upload_key: str, debug: bool, verbose: bool):
    test = os.environ.get('OORT_TESTS') == '1'
    kwargs = {'debug': debug, 'test': test, 'verbose': verbose, 'organisation': org_subdomain}

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


def parse_upload_watch_options(organisation: Optional[str] = None,
                               telescope: Optional[str] = None,
                               debug: Optional[bool] = False,
                               verbose: Optional[bool] = False):
    telescope_uuid = telescope or ''
    org_subdomain = organisation or ''

    # Validation of the organisation #

    org = None
    org_role = ''
    if org_subdomain:
        # Check that the provided subdomain corresponds to an existing remote organisation.
        org = check_remote_organisation(org_subdomain, debug, verbose)
        # Check that the provided subdomain is an organisation of which the current logged in astronomer is a member.
        org_role = check_local_astronomer_remote_organisation_membership(org_subdomain, debug, verbose)

    # Validation of the telescope #

    # In every case, check for telescope details if a UUID is provided.
    telescope_details = None
    if telescope_uuid:
        telescope_details = check_telescope(telescope_uuid, org_subdomain, debug, verbose)

    # Validation of the uploader #

    username = ''
    upload_key = ''
    # custom_astronomer = False

    # --- for when we will deal with custom astronomers
    # No custom astronomer for uploading. If no org, fine. If an org, one needs the telescope.
    # if astronomer == (None, None):

    # Fetch the username of the currently logged in astronomer.
    username, upload_key = check_local_astronomer(debug, verbose)
    if not username or not upload_key:
        raise InvalidWatchOptionsOortCloudError('Missing username or upload_key.')

    # If we have an organisation and no telescope UUID, we list the one available
    # and then raise an error
    if org is not None and telescope_details is None:
        list_organisation_telescopes(org_subdomain, debug, verbose)
        raise InvalidWatchOptionsOortCloudError('For an organisation, a telescope UUID must be provided.')

    # --- for when we will deal with custom astronomers
    # We have a custom astronomer. Check that the organisation is allowed to upload on behalf of it.
    # else:
    #     custom_astronomer = True
    #     username, upload_key = astronomer
    #     # Make sure the remote astronomer actually exists.
    #     check_remote_astronomer(username, upload_key, debug, verbose)
    #
    #     if org is None:
    #         raise InvalidWatchOptionsOortCloudError(
    #             'To check the custom astronomer, one needs the uploading organisation'
    #         )
    #
    #     # Check that the custom astronomer has a valid upload_key for the given organisation.
    #     # This is where the knot is. This check can only be made by a member of the registered organisation.
    #     check_organisation_shared_keys(org_subdomain, username, upload_key, debug, verbose)

    return username, upload_key, org_subdomain, org_role, telescope_details


def save_upload_folders(folders: list,
                        username: str,
                        upload_key: str,
                        org_subdomain: Optional[str],
                        org_role: Optional[str],
                        telescope_details: Optional[dict],
                        zip: bool,
                        debug: bool,
                        verbose: bool) -> list:
    logger = get_oort_logger('cli', debug=debug)

    prepared_folders = []
    for raw_folder in folders:
        upload_path = pathlib.Path(raw_folder).resolve()

        if not upload_path.exists() and os.environ.get('OORT_TESTS') != '1':
            logger.warn(f'Upload folder "{upload_path}" does not exists. Skipping.')
            continue

        if upload_path.is_file():
            upload_path = upload_path.parent

        telescope_uuid = ''
        if telescope_details:
            telescope_uuid = telescope_details.get('uuid') or ''

        identity = Identity(username=username,
                            upload_key=upload_key or '',
                            subdomain=org_subdomain or '',
                            role=org_role or '',
                            telescope=telescope_uuid,
                            zip=zip,
                            debug=debug)

        identity.save_with_folder(upload_folder_path=str(upload_path))
        prepared_folders.append((str(upload_path), identity))

    return prepared_folders
