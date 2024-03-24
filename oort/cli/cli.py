import click
from arcsecond import ArcsecondAPI, ArcsecondConfig, cli as ArcsecondCLI
from arcsecond.options import State

from oort import __version__
from oort.common.context import Context
from oort.common.utils import build_endpoint_kwargs
from oort.uploader.walker import walk
from .errors import OortCloudError, InvalidUploadOptionsOortCloudError
from .helpers import display_command_summary
from .options import basic_options

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
    config = ArcsecondConfig(state)
    _, error = ArcsecondAPI(config).login(username, password, upload_key=True)
    if error:
        click.echo(error)
    else:
        username = config.username
        click.echo(f' • Successfully logged in as @{username} (API: {state.api_name}).')


@main.command(help='Get or set the API server address (fully qualified domain name).')
@click.argument('name', required=False, nargs=1)
@click.argument('fqdn', required=False, nargs=1)
@pass_state
def api(state, name=None, fqdn=None):
    ArcsecondCLI.api(state, name, fqdn)


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
    dataset_list, error = ArcsecondAPI(ArcsecondConfig(state)).datasets.list()
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
@click.option('-d', '--dataset',
              required=True, nargs=1, type=click.STRING,
              help="The UUID or name of the dataset to put data in.")
@click.option('-o', '--organisation',
              required=False, nargs=1,
              help="The subdomain, if uploading for an Observatory Portal.")
@basic_options
@pass_state
def upload(state, folder, dataset=None, organisation=None):
    """
    Upload the content of a folder.

    You will be prompted for confirmation before the whole walking process actually
    start.

    Every DataFile must belong to a Dataset. If you provide a Dataset UUID, Oort will
    append files to the dataset. If you provide a Dataset *name*, Oort will try to find
    an existing Dataset with that name. If none could be found, Oort will create one,
    and put files in it.

    You can use `oort datasets [OPTIONS]` to get a list of your existing datasets
    (with their UUID).

    Oort will then start walking through the folder tree and uploads regular files
    (hidden and empty files will be skipped).
    """
    config = ArcsecondConfig(state)
    context = Context(config, dataset_uuid_or_name=dataset, subdomain=organisation)

    try:
        context.validate()
    except InvalidUploadOptionsOortCloudError as e:
        click.echo(f"\n • ERROR {str(e)} \n")
        return

    display_command_summary(context, [folder, ])
    ok = input('\n   ----> OK? (Press Enter) ')

    if ok.strip() == '':
        walk(context, folder)
