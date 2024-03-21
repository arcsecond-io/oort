import click
from arcsecond import ArcsecondAPI

from oort import __version__
from oort.common.config import (update_oort_config_upload_folder_sections_key)
from .errors import OortCloudError, InvalidUploadOptionsOortCloudError
from .helpers import display_command_summary, build_endpoint_kwargs
from .options import State, basic_options
from .validators import parse_upload_watch_options

pass_state = click.make_pass_decorator(State, ensure=True)

VERSION_HELP_STRING = "Show the Oort Cloud version and exit."
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help=VERSION_HELP_STRING)
@basic_options
@click.pass_context
def main(ctx, version=False, **kwargs):
    """
    Oort-Cloud ('oort' command) is a super-easy upload manager for arcsecond.io.

    Oort-Cloud is a pure "upward" tool, not a two-ways syncing tool. A file that
    is deleted locally will remain in the cloud if already uploaded. Change
    of files in the cloud have no effect locally either.

    Oort-Cloud uploads every non-hidden non-empty files. Make sure to not watch
    nor upload your home folder, or a folder containing sensitive information.

    Oort will upload files with enough metadata for Arcsecond to reproduce the
    local folder structure. Of course, the cleaner the local folders structure,
    the cleaner it will appear in Arcsecond.io.

    Oort-Cloud v2 works only with one direct mode (a whole new local monitor is
    in preparation). This direct mode (command `oort upload ...`) uploads files
    immediately, and returns.
    """
    if version:
        click.echo(__version__)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.option('--username', required=True, nargs=1, prompt=True,
              help="Username of the Arcsecond account. Primary email address is also allowed.")
@click.option('--password', required=True, nargs=1, prompt=True, hide_input=True,
              help="Password of the Arcsecond account. It will be sent encrypted.")
@basic_options
@pass_state
def login(state, username, password):
    """Login to your personal Arcsecond.io account.

    It also fetches your personal Upload key. This Upload key is a secret token
    which gives just enough permission to perform the upload of files and the
    minimum of metadata.

    Beware that the Upload key will be stored locally on a file:
    ~/.config/arcsecond/config.ini

    This Upload key is not your full API key. When logging in with oort, no fetch
    nor storage of the API key occur (only the Upload one).
    """
    _, error = ArcsecondAPI.login(username, password, upload_key=True, api=state.api_name)
    if error:
        click.echo(error)
    else:
        username = ArcsecondAPI.username(api=state.api_name)
        click.echo(f' • Successfully logged in as @{username} (API: {state.api_name}).')
        # Update all upload_key stored in the config for all watched folders.
        update_oort_config_upload_folder_sections_key(ArcsecondAPI.upload_key(api=state.api_name))


@main.command()
@click.argument('name', required=True, nargs=1)
@click.argument('address', required=False, nargs=1)
@pass_state
def api(state, name=None, address=None):
    """
    Configure the API server address.

    For instance:

    • "oort api main" to get the main API server address (default).\n
    • "oort api dev http://localhost:8000" to configure a dev server.

    You can then use --api <api name> in every command to choose which API
    server you want to interact with. Hence, "--api dev" will choose the above
    dev server.
    """
    if address is None:
        print(ArcsecondAPI.get_api_name(api_name=name))
    else:
        ArcsecondAPI.set_api_name(address, api_name=name)


@main.command(help="Display the list of (organisation) telescopes.")
@click.option('-o', '--organisation',
              required=False, nargs=1,
              help="The subdomain, if uploading to an organisation (Observatory Portal).")
@basic_options
@pass_state
def telescopes(state, organisation=None):
    org_subdomain = organisation or ''
    if org_subdomain:
        click.echo(f" • Fetching telescopes for organisation {org_subdomain}...")
    else:
        click.echo(" • Fetching telescopes...")

    kwargs = build_endpoint_kwargs(state.api_name, subdomain=organisation)
    telescope_list, error = ArcsecondAPI.telescopes(**kwargs).list()
    if error is not None:
        raise OortCloudError(str(error))

    if isinstance(telescope_list, dict) and 'results' in telescope_list.keys():
        telescope_list = telescope_list['results']

    click.echo(f" • Found {len(telescope_list)} telescope{'s' if len(telescope_list) > 1 else ''}.")
    for telescope_dict in telescope_list:
        s = f" 🔭 \"{telescope_dict['name']}\" "
        if telescope_dict['alias']:
            s += f"alias \"{telescope_dict['alias']}\" "
        s += f"(uuid: {telescope_dict['uuid']}) "
        # s += f"[ObservingSite UUID: {telescope_dict['observing_site']}]"
        click.echo(s)


@main.command(help="Display the list of (organisation) datasets.")
@click.option('-o', '--organisation',
              required=False, nargs=1,
              help="The subdomain, if uploading to an organisation (Observatory Portal).")
@basic_options
@pass_state
def datasets(state, organisation=None):
    org_subdomain = organisation or ''
    if org_subdomain:
        click.echo(f" • Fetching datasets for organisation '{org_subdomain}'...")
    else:
        click.echo(" • Fetching datasets...")

    kwargs = build_endpoint_kwargs(state.api_name, subdomain=organisation)
    dataset_list, error = ArcsecondAPI.datasets(**kwargs).list()
    if error is not None:
        raise OortCloudError(str(error))

    if isinstance(dataset_list, dict) and 'results' in dataset_list.keys():
        dataset_list = dataset_list['results']

    click.echo(f" • Found {len(dataset_list)} dataset{'s' if len(dataset_list) > 1 else ''}.")
    for dataset_dict in dataset_list:
        s = f" 💾 \"{dataset_dict['name']}\" "
        s += f"(uuid: {dataset_dict['uuid']}) "
        # s += f"[ObservingSite UUID: {telescope_dict['observing_site']}]"
        click.echo(s)


@main.command(help='Directly upload a folder\'s content.')
@click.argument('folder', required=True, nargs=1)
@click.option('-o', '--organisation',
              required=False, nargs=1,
              help="The subdomain, if uploading for an Observatory Portal.")
@click.option('-t', '--telescope',
              required=False, nargs=1, type=click.STRING,
              help="The UUID or alias of the telescope acquiring the data (mandatory only for Portal uploads).")
@click.option('-d', '--dataset',
              required=False, nargs=1, type=click.STRING,
              help="The UUID or name of the dataset to put data in.")
@click.option('-f', '--force',
              required=False, nargs=1, type=click.BOOL, is_flag=True,
              help="Force the re-uploading of folder's data, resetting the local Uploads information. Default is False.")
@basic_options
@pass_state
def upload(state, folder, organisation=None, telescope=None, dataset=None, force=False):
    """
    Upload the content of a folder.

    If an organisation is provided, a telescope UUID must also be provided.

    Oort will start by walking through the folder tree and uploads files
    according to the name of the subfolders (see main help). Once done,
    every new file created in the folder tree will trigger a sync + upload
    process.
    """
    try:
        identity = parse_upload_watch_options(organisation, telescope, dataset, state.api_name)
    except InvalidUploadOptionsOortCloudError as e:
        click.echo(f"\n • ERROR {str(e)} \n")
        return

    display_command_summary([folder, ], identity)
    ok = input('\n   ----> OK? (Press Enter) ')

    if ok.strip() == '':
        from oort.uploader.walker import walk

        walk(folder, identity, bool(force))
