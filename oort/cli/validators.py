import os
import uuid
from typing import Optional, Union

import click
from arcsecond import ArcsecondAPI
from click import UUID

from .errors import (
    InvalidAstronomerOortCloudError,
    InvalidOrgMembershipOortCloudError,
    InvalidOrganisationTelescopeOortCloudError,
    InvalidTelescopeOortCloudError,
    InvalidWatchOptionsOortCloudError,
    UnknownOrganisationOortCloudError,
    InvalidOrganisationDatasetOortCloudError,
    InvalidDatasetOortCloudError,
    InvalidUploadOptionsOortCloudError
)
from .helpers import build_endpoint_kwargs
from .identity import Identity


def __validate_remote_organisation(org_subdomain: str, api: str = 'main') -> dict:
    click.echo(f" • Fetching details of organisation {org_subdomain}...")

    # Do NOT include subdomain since we want to access the public endpoint of the list of organisations here.
    # Including the subdomain kwargs would filter the result for that organisation.
    # Which would make no sense, since there is no list of organisations for a given organisation...
    kwargs = build_endpoint_kwargs(api)
    org_details, error = ArcsecondAPI.organisations(**kwargs).read(org_subdomain)
    if error is not None:
        raise UnknownOrganisationOortCloudError(org_subdomain, str(error))

    return org_details


def __validate_astronomer_role_in_remote_organisation(org_subdomain: str, api: str = 'main') -> str:
    # Do NOT include subdomain since we want the global list of memberships of the profile here.
    # An alternative would be to fetch the list of members of a given organisation and see if the profile
    # is inside. But there is actually no need to fetch anything since the memberships are included in
    # the profile of the user logged in.
    kwargs = build_endpoint_kwargs(api)
    # Reading local memberships if an org_subdomain is provided.
    memberships = ArcsecondAPI.memberships(**kwargs) if org_subdomain else None

    # An org_subdomain is provided, but memberships are empty.
    if org_subdomain and memberships in [None, {}]:
        raise InvalidOrgMembershipOortCloudError(org_subdomain)

    # Ok, an org_subdomain is provided and memberships are not empty. Checking for membership
    # of that org_subdomain AND checking it is at least a member (not a visitor).
    role = memberships.get(org_subdomain, None)
    if not role or role not in ['member', 'admin', 'superadmin']:
        raise InvalidOrgMembershipOortCloudError(org_subdomain)

    return role


def __print_organisation_telescopes(org_subdomain: str, api: str = 'main') -> None:
    click.echo(f" • Here is a list of existing telescopes for organisation '{org_subdomain}':")
    kwargs = build_endpoint_kwargs(api, org_subdomain)
    telescope_list, error = ArcsecondAPI.telescopes(**kwargs).list()
    for telescope in telescope_list:
        s = f" 🔭 {telescope['name']}"
        if telescope.get('alias', ''):
            s += f" a.k.a. {telescope['alias']}"
        s += f" ({telescope['uuid']})"
        click.echo(s)


# The organisation is actually optional. It allows to check for a telescope
# also in the case of an individual astronomer.
def __validate_telescope_uuid(telescope_uuid_or_alias: Union[str, UUID],
                              org_subdomain: Optional[str],
                              api: str = 'main') -> Optional[dict]:
    click.echo(f" • Fetching details of telescope {telescope_uuid_or_alias}...")

    # To the contrary of datasets, telescope models have a field 'alias', and it also works for
    # reading telescope details in /telescopes/<uuid_or_alias>/, even for organisations.
    # Hence, a single "read" is enough to find out if the telescope exists.
    kwargs = build_endpoint_kwargs(api, org_subdomain)
    telescope_detail, error = ArcsecondAPI.telescopes(**kwargs).read(str(telescope_uuid_or_alias))
    if error is not None:
        if org_subdomain:
            raise InvalidOrganisationTelescopeOortCloudError(str(telescope_uuid_or_alias), org_subdomain, str(error))
        else:
            raise InvalidTelescopeOortCloudError(str(telescope_uuid_or_alias), str(error))

    # Will contain UUID, name and alias.
    return telescope_detail


# The organisation is actually optional. It allows to check for a dataset
# also in the case of an individual astronomer.
def __validate_dataset_uuid(dataset_uuid_or_name: Union[str, UUID],
                            org_subdomain: Optional[str],
                            api: str = 'main') -> Optional[dict]:
    kwargs = build_endpoint_kwargs(api, org_subdomain)
    dataset = None

    try:
        uuid.UUID(dataset_uuid_or_name)
    except ValueError:
        click.echo(f" • Parameter {dataset_uuid_or_name} is not an UUID. Looking for a dataset with that name...")
        datasets_list, error = ArcsecondAPI.datasets(**kwargs).list({'name': dataset_uuid_or_name})
        if len(datasets_list) == 0:
            click.echo(f" • No dataset with name {dataset_uuid_or_name} found. It will be created.")
            dataset = {'name': dataset_uuid_or_name}
        elif len(datasets_list) == 1:
            click.echo(f" • One dataset known with name {dataset_uuid_or_name}. Data will be appended to it.")
            dataset = datasets_list[0]
        else:
            error = f"Multiple datasets with name containing {dataset_uuid_or_name} found. Be more specific."
    else:
        click.echo(f" • Fetching details of dataset {dataset_uuid_or_name}...")
        dataset, error = ArcsecondAPI.datasets(**kwargs).read(str(dataset_uuid_or_name))

    if error is not None:
        if org_subdomain:
            raise InvalidOrganisationDatasetOortCloudError(str(dataset_uuid_or_name), org_subdomain, str(error))
        else:
            raise InvalidDatasetOortCloudError(str(dataset_uuid_or_name), str(error))

    return dataset


def ___read_local_astronomer_credentials(api: str):
    test = os.environ.get('OORT_TESTS') == '1'

    username = ArcsecondAPI.username(test=test, api=api)
    if username is None:
        raise InvalidAstronomerOortCloudError('')

    upload_key = ArcsecondAPI.upload_key(test=test, api=api)
    return username, upload_key


def parse_upload_watch_options(subdomain: str = '',
                               telescope_uuid_or_name: str = '',
                               dataset_uuid_or_name: str = '',
                               api: str = 'main') -> Identity:
    assert api != '' and api is not None

    username, upload_key = ___read_local_astronomer_credentials(api)
    if not username or not upload_key:
        raise InvalidWatchOptionsOortCloudError('Missing username or upload_key.')

    organisation = None
    if subdomain:
        __validate_remote_organisation(subdomain, api)
        role = __validate_astronomer_role_in_remote_organisation(subdomain, api)
        organisation = {'subdomain': subdomain, 'role': role}

    telescope = None
    if telescope_uuid_or_name:
        telescope = __validate_telescope_uuid(telescope_uuid_or_name, subdomain, api)

    if subdomain and not telescope_uuid_or_name:
        __print_organisation_telescopes(subdomain, api)
        raise InvalidUploadOptionsOortCloudError('For an organisation, a telescope UUID (or alias) must be provided.')

    dataset = None
    if dataset_uuid_or_name:
        dataset = __validate_dataset_uuid(dataset_uuid_or_name, subdomain, api)

    identity = Identity(username, upload_key, organisation, telescope, dataset, api)

    return identity
