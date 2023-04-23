import importlib
import os
import subprocess

import click
from arcsecond import ArcsecondAPI

from oort import __version__
from oort.cli.folders import (parse_upload_watch_options, save_upload_folders)
from oort.cli.helpers import display_command_summary
from oort.cli.options import State, basic_options
from oort.cli.supervisor import (get_supervisor_processes_status, get_supervisor_config)
from oort.monitor.errors import InvalidWatchOptionsOortCloudError
from oort.shared.config import (get_oort_config_upload_folder_sections,
                                remove_oort_config_folder_section,
                                update_oort_config_upload_folder_sections_key)
from oort.shared.constants import OORT_UPLOADER_FOLDER_DETECTION_TICK_SECONDS
from oort.shared.errors import OortCloudError

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

    Oort-Cloud has 2 modes: direct, and batch. As of now, the two modes are
    exclusive (because of the access to the small local SQLite database). You
    must **not** have oort batch mode running if you want to use the direct
    mode.

    The direct mode (command `oort upload ...`) uploads files immediately, and
    returns.

    The batch mode (with the command `oort watch...`) watches folders you
    indicate, and automatically upload all files contained in the folder
    (and its subfolders). It keeps running in the background, and as soon a
    new file appears in the folder tree, Oort will upload it.

    The batch mode works by managing 2 processes:\n
    • An uploader, which takes care of creating/syncing the right Dataset and
        Datafile objects in Arcsecond.io (either in your personal account, or
        your Organisation). And then upload the real files.\n
    • A small web server, which allow you to monitor, control and setup what is
        happening in the uploader (and also see what happened before).
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


@main.command(help='Start one of the Oort service: uploader or monitor.')
@click.argument('service', required=True, type=click.Choice(['uploader', 'monitor'], case_sensitive=False))
@basic_options
@pass_state
def start(state, service):
    spec = importlib.util.find_spec('oort')
    command_path = os.path.join(os.path.dirname(spec.origin), service, 'main.py')
    # Making sure they are executable
    os.chmod(command_path, 0o744)
    subprocess.run(command_path)


@main.command(help='Display the supervisord config.')
@basic_options
@pass_state
def config(state):
    print("\nBelow is the supervisord config you should use if you want supervisor to manage Oort processes:\n")
    print(get_supervisor_config())


@main.command(help="Display the list of all watched folders and their options.")
@basic_options
@pass_state
def folders(state):
    sections = get_oort_config_upload_folder_sections()
    if len(sections) == 0:
        click.echo(" • No folder watched. Use `oort watch` (or `oort watch --help` for more details).")
    else:
        for section in sections:
            section_hash = section.get('section').replace('watch-folder-', '')
            click.echo(f" • Folder ID \"{section_hash}\"")
            click.echo(f"   username     = @{section.get('username')}")
            click.echo(f"   upload_key   = {section.get('upload_key')[0:4]}••••")
            if section.get('subdomain'):
                click.echo(f"   organisation = {section.get('subdomain')} (role: {section.get('role')})")
            else:
                click.echo("   organisation = (no organisation)")
            if section.get('telescope'):
                click.echo(f"   telescope    = {section.get('telescope')}")
            else:
                click.echo("   telescope    = (no telescope)")
            click.echo(f"   path         = {section.get('path')}")
            click.echo(f"   zip          = {section.get('zip', 'False')}")
            click.echo()


@main.command(help="Display the list of (organisation) telescopes.")
@click.option('-o', '--organisation',
              required=False, nargs=1,
              help="The Organisation subdomain, if uploading to an organisation.")
@basic_options
@pass_state
def telescopes(state, organisation=None):
    test = os.environ.get('OORT_TESTS') == '1'
    kwargs = {'api': state.api_name, 'test': test, 'upload_key': ArcsecondAPI.upload_key(api=state.api_name)}

    org_subdomain = organisation or ''
    if org_subdomain:
        kwargs.update(organisation=org_subdomain)
        click.echo(f" • Fetching telescopes for organisation {org_subdomain}...")
    else:
        click.echo(" • Fetching telescopes...")

    telescope_list, error = ArcsecondAPI.telescopes(**kwargs).list()
    if error is not None:
        raise OortCloudError(str(error))

    click.echo(f" • Found {len(telescope_list)} telescope{'s' if len(telescope_list) > 1 else ''}.")
    for telescope_dict in telescope_list:
        s = f" 🔭 \"{telescope_dict['name']}\" "
        if telescope_dict['alias']:
            s += f"alias \"{telescope_dict['alias']}\" "
        s += f"(uuid: {telescope_dict['uuid']}) "
        # s += f"[ObservingSite UUID: {telescope_dict['observing_site']}]"
        click.echo(s)


@main.command(help='Directly upload a folder\'s content.')
@click.argument('folder', required=True, nargs=1)
@click.option('-o', '--organisation',
              required=False, nargs=1,
              help="The Organisation subdomain, if uploading to an organisation.")
@click.option('-t', '--telescope',
              required=False, nargs=1, type=click.STRING,
              help="The UUID or the alias of the telescope acquiring the data (mandatory only for organisation "
                   "uploads).")
@click.option('-f', '--force',
              required=False, nargs=1, type=click.BOOL, is_flag=True,
              help="Force the re-uploading of folder's content, resetting the local Uploads information. Default is "
                   "False.")
@click.option('-z', '--zip',
              required=False, nargs=1, type=click.BOOL, is_flag=True,
              help="Zip the data files (FITS and XISF) before sending to the cloud. Default is False.")
@basic_options
@pass_state
def upload(state, folder, organisation=None, telescope=None, force=False, zip=False):
    """
    Upload the content of a folder.

    If an organisation is provided, a telescope UUID must also be provided.

    Oort will start by walking through the folder tree and uploads files
    according to the name of the subfolders (see main help). Once done,
    every new file created in the folder tree will trigger a sync + upload
    process.
    """
    click.echo(f"\n{80 * '*'}")
    click.echo(" • DIRECT MODE: command will not return until it has completed the upload of folder's files.")
    click.echo(" • DIRECT MODE: for a folder with a large volume of files, it may take some time to finish.")
    click.echo(f"{80 * '*'}\n")

    try:
        identity = parse_upload_watch_options(organisation, telescope, zip, state.api_name)
    except InvalidWatchOptionsOortCloudError:
        return

    display_command_summary([folder, ], identity)
    ok = input('\n   ----> OK? (Press Enter) ')

    if ok.strip() == '':
        from oort.uploader.engine.walker import walk

        walk(folder, identity, bool(force))


@main.command(help='Start watching a folder content for uploading files in batch/background mode.')
@click.argument('folders', required=True, nargs=-1)
@click.option('-o', '--organisation',
              required=False, nargs=1,
              help="The Organisation subdomain, if uploading to an organisation.")
@click.option('-t', '--telescope',
              required=False, nargs=1, type=click.STRING,
              help="The UUID or the alias of the telescope acquiring data (in the case of organisation uploads).")
@click.option('-z', '--zip', is_flag=True,
              required=False, nargs=1, type=click.BOOL,
              help="Zip the data files (FITS and XISF) before sending to the cloud. Default is False.")
@basic_options
@pass_state
def watch(state, folders, organisation=None, telescope=None, zip=False):
    """
    Indicate a folder (or multiple folders) that Oort should watch. The files of the
    folder and all of its subfolders will be uploaded (expect hidden files).

    If an organisation is provided, a telescope UUID must also be provided.

    Oort will start by walking through the folder tree and uploads files
    according to the name of the subfolders (see main help). Once done,
    every new file created in the folder tree will trigger a sync + upload
    process.
    """
    click.echo(f"\n{80 * '*'}")
    click.echo(" • BATCH MODE: command will give the prompt back, and uploads will occur in the background.")
    click.echo(" • BATCH MODE: use the monitor to follow the progress (`oort start monitor`).")
    click.echo(f"{80 * '*'}\n")

    try:
        identity = parse_upload_watch_options(organisation, telescope, zip, state.api_name)
    except InvalidWatchOptionsOortCloudError:
        return

    display_command_summary(folders, identity)
    ok = input('\n   ----> OK? (Press Enter) ')

    if ok.strip() == '':
        save_upload_folders(folders, identity)
        click.echo("\n • OK.")
        msg = f" • Oort will start watching within {OORT_UPLOADER_FOLDER_DETECTION_TICK_SECONDS} seconds "
        msg += "if the uploader process is running.\n • Getting the processes status for you right now:"
        click.echo(msg)
        get_supervisor_processes_status()


@main.command(help="Remove (a) folder(a) from the watched folder list.")
@click.argument('folder_id', required=True, type=str, nargs=-1)
@basic_options
@pass_state
def unwatch(state, folder_id):
    """Print INDEX.

    INDEX is the folder index in the list. Use `oort folders` *every time* to list them all.
    """
    sections = get_oort_config_upload_folder_sections()
    sections_mapping = {section.get('section').replace('watch-folder-', ''): section for section in sections}
    clean_folder_ids = set(folder_id)
    for clean_id in clean_folder_ids:
        if clean_id in sections_mapping.keys():
            result = remove_oort_config_folder_section(sections_mapping[clean_id]['section'])
            click.echo(f' • Folder ID {clean_id} removed with success: {result}.')
        else:
            click.echo(f' • Folder ID {clean_id} unknown/invalid. Skipped.')
