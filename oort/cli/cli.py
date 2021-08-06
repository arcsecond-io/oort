import builtins
import os
import webbrowser

import click
from arcsecond import ArcsecondAPI

from oort import __version__
from oort.cli.folders import (parse_upload_watch_options, save_upload_folders)
from oort.cli.options import State, basic_options
from oort.cli.supervisor import (get_supervisor_processes_status,
                                 reconfigure_supervisor,
                                 start_supervisor_daemon,
                                 start_supervisor_processes,
                                 stop_supervisor_daemon,
                                 stop_supervisor_processes)
from oort.server.errors import InvalidWatchOptionsOortCloudError
from oort.shared.config import (get_config_upload_folder_sections,
                                get_config_value,
                                get_log_file_path,
                                get_supervisor_conf_file_path,
                                update_config_upload_folder_sections_key)
from oort.shared.errors import OortCloudError
from oort.shared.utils import tail
from oort.uploader.main import paths_observer

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

    It watches folders you indicates, and automatically upload all files
    contained in the folder (and its subfolders). As soon a new file appears
    in the folder tree, Oort will upload it.

    Oort-Cloud is a pure push up tool, not a two-way syncing tool. A file that
    is deleted locally will remain in the cloud if already uploaded. Change
    of files in the cloud have no effect locally either.

    *** Oort is using the folder structure to infer the type and organisation
    of files. ***

    Structure is as follow: Night Logs contain multiple Observations and/or
    Calibrations. And to each Observation and Calibration is attached a Dataset
    containing the files.

    If a folder contains the word "Bias" or "Dark" or "Flat" or "Calib" (all
    case-insensitive), the files inside it will be put inside a Calibration
    object, associated with a Dataset whose name is that of the folder.

    Folders not containing any of these keywords are considered as target names.
    Their files will be put inside a Dataset of that name, inside an
    Observation.

    To form the Dataset and Observation / Calibration names, Oort uses
    the complete subfolder path string, making the original filesystem structure
    "visible" in the Arcsecond webpage.

    For instance, FITS or XISF files found in "<root>/NGC3603/mosaic/Halpha"
    will be put in an Observation (not a Calibration, there is no special
    keyword found), and its Dataset will be named identically
    "NGC3603/mosaic/Halpha".

    All Calibrations and Observations are automatically associated with
    Night Logs whose date is inferred from the observation date of the files.
    Oort takes automatically care of the right "date" whether the file is taken
    before or after noon on that local place. In other words, the "night"
    boundaries are running from local noon to the next local noon.

    Oort-Cloud works by managing 2 processes:\n
    • An uploader, which takes care of creating/syncing the right Night Log,
        Observation and Calibration objects, as well as Dataset and Datafile
        objects in Arcsecond.io (either in your personal account, or your
        Organisation). And then upload the real files.\n
    • A small web server, which allow you to monitor, control and setup what is
        happening in the uploader (and also see what happened before).

    The `oort` command is dedicated to start, stop and get status
    of these two processes. Once they are up and running, the only one thing
    you have to do is to indicate which folders `oort` should watch
    to find files to upload. Use `oort watch` for that.
    """
    if version:
        click.echo(__version__)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.option('--username', required=True, nargs=1, prompt=True)
@click.option('--password', required=True, nargs=1, prompt=True, hide_input=True)
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
    _, error = ArcsecondAPI.login(username, password, None, upload_key=True, debug=state.debug, verbose=state.verbose)
    if error is not None:
        click.echo(error)
    else:
        click.echo(f' • Successfully logged in as @{username}.')
        update_config_upload_folder_sections_key(ArcsecondAPI.upload_key())


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


@main.command(help='Stop Oort processes.')
@basic_options
@pass_state
def stop(state):
    stop_supervisor_processes(debug=state.debug)


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
    host = get_config_value('server', 'host')
    port = get_config_value('server', 'port')
    webbrowser.open(f"http://{host}:{port}")


@main.command(help='Display the tail of the Oort logs.')
@click.option('-n', required=False, nargs=1, type=click.INT, help="The number of (last) lines to show (Default: 10).")
@basic_options
@pass_state
def logs(state, n):
    with builtins.open(get_log_file_path(), 'r') as f:
        print(''.join(tail(f, n or 10)))


@main.command(help='Display the supervisord config.')
@basic_options
@pass_state
def config(state):
    with builtins.open(get_supervisor_conf_file_path(), 'r') as f:
        print(f.read())


@main.command()
@click.argument('folders', required=True, nargs=-1)
@click.option('-o', '--organisation',
              required=False,
              nargs=1,
              help="The Organisation subdomain, if uploading to an organisation.")
@click.option('-t', '--telescope',
              required=False,
              nargs=1,
              type=click.UUID,
              help="The UUID of the telescope acquiring data (in the case of organisation uploads).")
@click.option('--astronomer',
              required=False,
              nargs=2,
              type=(str, str),
              default=[None, None],
              help="A astronomer on behalf of whom you upload. You MUST provide its username and api key.")
@basic_options
@pass_state
def watch(state, folders, o=None, organisation=None, t=None, telescope=None, astronomer=(None, None)):
    """
    Indicate a folder (or multiple folders) that Oort should watch.

    If an organisation is provided, a telescope UUID must also be provided.

    If an organisation is provided, no custom astronomer can be used. Inversely,
    if a custom astronomer is provided, no organisation can be used.

    Oort will start by walking through the folder tree and uploads files
    according to the name of the subfolders (see main help). Once done,
    every new file created in the folder tree will trigger a sync + upload
    process.
    """
    try:
        username, upload_key, org_subdomain, org_role, telescope_details = \
            parse_upload_watch_options(o, organisation, t, telescope, astronomer, state.debug, state.verbose)
    except InvalidWatchOptionsOortCloudError:
        return

    click.echo(" --- Folder(s) watch summary --- ")
    click.echo(f" • Arcsecond username: @{username} (Upload key: {upload_key[:4]}...)")
    if org_subdomain:
        click.echo(f" • Uploading for organisation: {org_subdomain} (role: {org_role})")
    else:
        click.echo(" • Uploading to a *personal* account (use option '-o <subdomain>' for an organisation).")

    if telescope_details:
        name, uuid = telescope_details.get('name'), telescope_details.get('uuid')
        click.echo(f" • Night Logs will be linked to telescope '{name}' ({uuid}).")
    else:
        click.echo(" • No designated telescope.")

    click.echo(" • Dates inside FITS/XISF files are assumed to be local dates.")

    if len(folders) == 1:
        click.echo(f" • Folder path: {os.path.expanduser(os.path.realpath(folders[0]))}")
    else:
        click.echo(" • Folder paths:")
        for folder in folders:
            click.echo(f"   > {os.path.expanduser(os.path.realpath(folder))}")

    ok = input(' --> OK? (Press Enter) ')

    if ok.strip() == '':
        oort_folder = os.path.dirname(os.path.dirname(__file__))
        prepared_folders = save_upload_folders(folders,
                                               username,
                                               upload_key,
                                               org_subdomain,
                                               org_role,
                                               telescope_details,
                                               state.debug,
                                               state.verbose)

        for (folder_path, identity) in prepared_folders:
            # paths_observer.observe_folder will deal with the initial walk.
            paths_observer.observe_folder(folder_path, identity)


@main.command(help="Display the list of all watched folders and their options.")
@basic_options
@pass_state
def folders(state):
    sections = get_config_upload_folder_sections()
    if len(sections) == 0:
        click.echo(" • No folder watched. Use `oort watch` (or `oort watch --help` for more details).")
    else:
        for index, section in enumerate(sections):
            click.echo(f" • Folder #{index + 1}:")
            click.echo(f"   username     = @{section.get('username')}")
            click.echo(f"   upload_key   = {section.get('upload_key')[0:4]}•••••••")
            if section.get('subdomain'):
                click.echo(f"   organisation = {section.get('subdomain')} (role: {section.get('role')})")
            else:
                click.echo("   organisation = (no organisation)")
            if section.get('telescope'):
                click.echo(f"   telescope    = {section.get('telescope')}")
            else:
                click.echo("   telescope    = (no telescope)")
            click.echo(f"   path         = {section.get('path')}")
            click.echo()


@main.command(help="Display the list of (organisation) telescopes.")
@click.option('-o', '--organisation',
              required=False,
              nargs=1,
              help="The Organisation subdomain, if uploading to an organisation.")
@basic_options
@pass_state
def telescopes(state, o=None, organisation=None):
    test = os.environ.get('OORT_TESTS') == '1'
    kwargs = {'debug': state.debug, 'test': test, 'verbose': state.verbose}

    org_subdomain = o or organisation or ''
    if org_subdomain:
        kwargs.update(organisation=org_subdomain)
        click.echo(f" • Fetching telescopes for organisation {org_subdomain}...")
    else:
        click.echo(f" • Fetching telescopes...")

    telescope_list, error = ArcsecondAPI.telescopes(**kwargs).list()
    if error:
        raise OortCloudError(str(error))

    click.echo(f" • Found {len(telescope_list)} telescope{'s' if len(telescope_list) > 1 else ''}.")
    for telescope_dict in telescope_list:
        s = f" 🔭 \"{telescope_dict['name']}\" (UUID: {telescope_dict['uuid']}) "
        s += f"[ObservingSite UUID: {telescope_dict['observing_site']}]"
        click.echo(s)
