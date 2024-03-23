import os
import uuid
from typing import Optional, Union

import click
from arcsecond import ArcsecondAPI, Config
from click import UUID

from .errors import (
    InvalidAstronomerOortCloudError,
    InvalidOrgMembershipOortCloudError,
    InvalidWatchOptionsOortCloudError,
    UnknownOrganisationOortCloudError,
    InvalidOrganisationDatasetOortCloudError,
    InvalidDatasetOortCloudError
)
from .options import State


def __validate_remote_organisation(state: State, org_subdomain: str):
    click.echo(f" • Fetching details of organisation {org_subdomain}...")

    # Do NOT include subdomain since we want to access the public endpoint of the list of organisations here.
    # Including the subdomain kwargs would filter the result for that organisation.
    # Which would make no sense, since there is no list of organisations for a given organisation...
    config = Config(state, org_subdomain, os.environ.get('OORT_TESTS') == '1')
    organisation, error = ArcsecondAPI(config).organisations.read(org_subdomain)
    if error is not None:
        raise UnknownOrganisationOortCloudError(org_subdomain, str(error))

    return organisation


def __validate_astronomer_role_in_remote_organisation(state: State, org_subdomain: str):
    config = Config(state, '', os.environ.get('OORT_TESTS') == '1')
    role = config.read_key(org_subdomain)
    if not role or role not in ['member', 'admin', 'superadmin']:
        raise InvalidOrgMembershipOortCloudError(org_subdomain)


# def __print_organisation_telescopes(org_subdomain: str, api: str = 'main'):
#     click.echo(f" • Here is a list of existing telescopes for organisation '{org_subdomain}':")
#     kwargs = build_endpoint_kwargs(api, org_subdomain)
#     telescope_list, error = ArcsecondAPI.telescopes(**kwargs).list()
#     for telescope in telescope_list:
#         s = f" 🔭 {telescope['name']}"
#         if telescope.get('alias', ''):
#             s += f" a.k.a. {telescope['alias']}"
#         s += f" ({telescope['uuid']})"
#         click.echo(s)


# The organisation is actually optional. It allows to check for a dataset
# also in the case of an individual astronomer.
def __validate_dataset_uuid(state: State, dataset_uuid_or_name: Union[str, UUID], org_subdomain: Optional[str]):
    config = Config(state, org_subdomain, os.environ.get('OORT_TESTS') == '1')
    dataset = None

    try:
        uuid.UUID(dataset_uuid_or_name)
    except ValueError:
        click.echo(f" • Parameter {dataset_uuid_or_name} is not an UUID. Looking for a dataset with that name...")
        datasets_list, error = ArcsecondAPI(config).datasets.list(**{'name': dataset_uuid_or_name})
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
        dataset, error = ArcsecondAPI(config).datasets.read(str(dataset_uuid_or_name))

    if error is not None:
        if org_subdomain:
            raise InvalidOrganisationDatasetOortCloudError(str(dataset_uuid_or_name), org_subdomain, str(error))
        else:
            raise InvalidDatasetOortCloudError(str(dataset_uuid_or_name), str(error))

    return dataset


def __validate_local_astronomer_credentials(state: State):
    test = os.environ.get('OORT_TESTS') == '1'

    username = Config(state, test=test).username
    if username is None:
        raise InvalidAstronomerOortCloudError('Missing username')

    upload_key = Config(state, test=test).upload_key
    if not upload_key:
        raise InvalidWatchOptionsOortCloudError('Missing upload_key.')


def validate_upload_parameters(state: State, dataset_uuid_or_name: str = '', subdomain: str = ''):
    values = {}

    __validate_local_astronomer_credentials(state)
    dataset = __validate_dataset_uuid(state, dataset_uuid_or_name, subdomain)
    values.update(dataset=dataset)

    if subdomain:
        organisation = __validate_remote_organisation(state, subdomain)
        values.update(organisation=organisation)

        __validate_astronomer_role_in_remote_organisation(state, subdomain)

    return values
