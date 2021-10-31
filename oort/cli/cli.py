import os
import webbrowser

import click
from arcsecond import ArcsecondAPI

from oort import __version__
from oort.cli.folders import (parse_upload_watch_options, save_upload_folders)
from oort.cli.helpers import display_command_summary
from oort.cli.options import State, basic_options
from oort.cli.supervisor import (get_supervisor_processes_status,
                                 reconfigure_supervisor,
                                 start_supervisor_daemon,
                                 start_supervisor_processes,
                                 stop_supervisor_daemon,
                                 stop_supervisor_processes)
from oort.server.errors import InvalidWatchOptionsOortCloudError
from oort.shared.config import (get_oort_config_upload_folder_sections,
                                get_oort_config_value,
                                get_oort_log_file_path,
                                get_oort_supervisor_conf_file_path,
                                update_oort_config_upload_folder_sections_key)
from oort.shared.constants import OORT_UPLOADER_FOLDER_DETECTION_TICK_SECONDS
from oort.shared.errors import OortCloudError
from oort.shared.identity import Identity
from oort.shared.utils import tail

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

    Oort-Cloud is a pure push up tool, not a two-way syncing tool. A file that
    is deleted locally will remain in the cloud if already uploaded. Change
    of files in the cloud have no effect locally either.

    Oort-Cloud uploads every non-hidden non-empty files. Make sure to not watch
    your home folder, or a folder with secret information.

    Oort is using one simple rule to group files inside datasets.
    ** One folder = One dataset. ** Of course, a sub(sub)folder is considered
    as a new folder.

    Hence, the cleaner the local folders structure, the cleaner it will appear
    in arcsecond.io.

    To each data file (FITS or XISF) will be associated an Observation or a
    Calibration. If a "OBJECT" field is found in the FITS or XISF header, it
    will be an Observation.

    If no "OBJECT" field can be found in the header, Oort will look at the
    folder path. If any of the word 'bias', 'dark', 'flat', 'calib' is present
    somewhere in the path, it will be a Calibration.

    Otherwise, it will be an Observation, whose target name will be that of the
    folder. However, if the folder name is some date in ISO-like format, it
    will be still considered a Calibration, since no sensible Target name
    could be found.

    Oort-Cloud has 2 modes: direct, and batch. As of now, the two modes are
    exclusive (because of the access to the small local SQLite database). You
    must **not** have oort batch mode running if you want to use the direct
    mode.

    The direct mode (command `oort upload ...`) uploads files immediately, and
    returns.

    The batch mode (with the command `oort watch...`) watches folders you
    indicates, and automatically upload all files contained in the folder
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

    It also fetch your personal Upload key. This Upload key is a secret token
    which gives just enough permission to perform the creation of Night Logs
    Observations, Calibrations, Datasets, Datafiles and perform the upload.
    Beware that the key will be stored locally on a file:
    ~/.arcsecond.ini
    """
    profile, error = ArcsecondAPI.login(username,
                                        password,
                                        None,
                                        upload_key=True,
                                        debug=state.debug,
                                        verbose=state.verbose)
    if error is not None:
        click.echo(error)
    else:
        click.echo(f' • Successfully logged in as @{ArcsecondAPI.username()}.')
        # Update all upload_key stored in the config for all watched folders.
        update_oort_config_upload_folder_sections_key(ArcsecondAPI.upload_key())


@main.command(help='Display current Oort processes status.')
@basic_options
@pass_state
def status(state):
    get_supervisor_processes_status(debug=state.debug)


@main.command(help='Start Oort processes.')
@basic_options
@pass_state
def start(state):
    start_supervisor_processes(debug=state.debug)
    get_supervisor_processes_status(debug=state.debug)


@main.command(help='Stop Oort processes.')
@basic_options
@pass_state
def stop(state):
    stop_supervisor_processes(debug=state.debug)
    get_supervisor_processes_status(debug=state.debug)


@main.command(help='Stop Oort process and deamon, reconfigure, and restart everything.')
@basic_options
@pass_state
def restart(state):
    stop_supervisor_processes(debug=state.debug)
    get_supervisor_processes_status(debug=state.debug)
    stop_supervisor_daemon(debug=state.debug)
    reconfigure_supervisor(debug=state.debug)
    start_supervisor_daemon(debug=state.debug)
    # start_supervisor_processes(debug=state.debug)
    get_supervisor_processes_status(debug=state.debug)


@main.command(help='Open Oort web URL in default browser')
@basic_options
@pass_state
def open(state):
    host = get_oort_config_value('server', 'host')
    port = get_oort_config_value('server', 'port')
    webbrowser.open(f"http://{host}:{port}")


@main.command(help='Display the tail of the Oort logs.')
@click.option('-n', required=False, nargs=1, type=click.INT, help="The number of (last) lines to show (Default: 10).")
@basic_options
@pass_state
def logs(state, n):
    with get_oort_log_file_path().open('r') as f:
        print(''.join(tail(f, n or 10)))


@main.command(help='Display the supervisord config.')
@basic_options
@pass_state
def config(state):
    with get_oort_supervisor_conf_file_path().open('r') as f:
        print(f.read())


@main.command(help="Display the list of all watched folders and their options.")
@basic_options
@pass_state
def folders(state):
    sections = get_oort_config_upload_folder_sections()
    if len(sections) == 0:
        click.echo(" • No folder watched. Use `oort watch` (or `oort watch --help` for more details).")
    else:
        for index, section in enumerate(sections):
            click.echo(f" • Folder #{index + 1}:")
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
    kwargs = {'debug': state.debug, 'test': test, 'verbose': state.verbose}

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
        s = f" >>> 🔭 \"{telescope_dict['name']}\" "
        if telescope_dict['alias']:
            s += f"alias \"{telescope_dict['alias']}\" "
        s += f"({telescope_dict['uuid']}) "
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
        username, upload_key, org_subdomain, org_role, telescope_details = \
            parse_upload_watch_options(organisation, telescope, state.debug, state.verbose)
    except InvalidWatchOptionsOortCloudError:
        return

    display_command_summary([folder, ], username, upload_key, org_subdomain, org_role, telescope_details, zip)

    ok = input('\n   ----> OK? (Press Enter) ')

    if ok.strip() == '':
        telescope_uuid = telescope_details['uuid'] if telescope_details is not None else None
        identity = Identity(username=username,
                            upload_key=upload_key,
                            subdomain=org_subdomain or '',
                            role=org_role or '',
                            telescope=telescope_uuid,
                            zip=zip,
                            debug=state.debug)

        from oort.uploader.engine.walker import walk

        walk(folder, identity, bool(force), debug=state.debug)


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
# @click.option('--astronomer',
#               required=False, nargs=2, type=(str, str), default=[None, None],
#               help="A astronomer on behalf of whom you upload. You MUST provide its username and upload key.")
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
    click.echo(" • BATCH MODE: use the monitor server to follow the progress (type `oort open` to open it).")
    click.echo(f"{80 * '*'}\n")

    try:
        username, upload_key, org_subdomain, org_role, telescope_details = \
            parse_upload_watch_options(organisation, telescope, state.debug, state.verbose)
    except InvalidWatchOptionsOortCloudError:
        return

    display_command_summary(folders, username, upload_key, org_subdomain, org_role, telescope_details, zip)

    ok = input('\n   ----> OK? (Press Enter) ')

    if ok.strip() == '':
        save_upload_folders(folders,
                            username,
                            upload_key,
                            org_subdomain,
                            org_role,
                            telescope_details,
                            zip,
                            state.debug,
                            state.verbose)

        click.echo("\n • OK.")
        msg = f" • Oort will start watching within {OORT_UPLOADER_FOLDER_DETECTION_TICK_SECONDS} seconds "
        msg += "if the uploader process is running.\n • Getting the processes status for you right now:"
        click.echo(msg)
        get_supervisor_processes_status(debug=state.debug)
