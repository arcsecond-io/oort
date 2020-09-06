import builtins
import os
import subprocess
import webbrowser

import click
from arcsecond import ArcsecondAPI

from oort import __version__
from oort.cli.folders import (check_astronomer_credentials,
                              check_astronomer_org_membership,
                              check_organisation,
                              check_organisation_local_membership,
                              check_organisation_telescope,
                              check_username,
                              list_organisation_telescopes,
                              save_upload_folders)
from oort.cli.options import State, basic_options
from oort.cli.supervisor import (get_supervisor_processes_status,
                                 reconfigure_supervisor,
                                 start_supervisor_daemon,
                                 stop_supervisor_daemon,
                                 stop_supervisor_processes,
                                 update_supervisor_processes)
from oort.shared.config import get_config_upload_folder_sections, get_config_value, get_log_file_path
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

    *** Oort is using the folder structure to infer the type and organisation
    of files. ***

    Structure is as follow: Night Logs contain multiple Observation and/or
    Calibrations. To each Observation and Calibration is attached a Dataset
    containing the files.

    For instance, if a folder contains the word "Bias" (case-insensitive), the
    files inside it will be put inside a Calibration object, associated with
    a Dataset whose name is that of the folder.

    Keywords directing files in Calibrations are "Bias", "Dark", "Flat" and
    "Calib". All other folder names are considered as target names, and put
    inside Observations.

    Complete subfolder names will be used as Dataset and Observation / Calibration
    names.

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
    • An uploader, which takes care of creating/syncing the right Night Logs,
        Observations and Calibrations, as well as Datasets and Datafiles in
        Arcsecond.io (either in your personal account, or your Organisation).
        And then upload the files.\n
    • A small web server, which allow you to monitor, control and setup what is
        happening in the uploader (and find what happened before too).

    The `oort` command is dedicated to start, stop and get status
    of these two processes. Once they are up and running, only ONE thing
    remain to be done by you: indicate which folders `oort` should watch
    to find files to upload.
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

    It also fetch your personal API key. This API key is a secret token
    you should take care. It will be stored locally on a file:
    ~/.arcsecond.ini

    Make sure to indicate the organisation subdomain if you intend to upload for that
    organisation.
    """
    ArcsecondAPI.login(username, password, None, debug=state.debug)


@main.command(help='Get Oort processes status.')
@basic_options
@pass_state
def status(state):
    get_supervisor_processes_status(debug=state.debug)


@main.command(help='Update Oort processes (for when you just upgraded Oort).')
@basic_options
@pass_state
def update(state):
    reconfigure_supervisor(debug=state.debug)
    update_supervisor_processes(debug=state.debug)
    # start_supervisor_daemon(debug=state.debug)


@main.command(help='Completely stop, reload and restart Oort daemon and processes.')
@basic_options
@pass_state
def restart(state):
    stop_supervisor_processes(debug=state.debug)
    get_supervisor_processes_status(debug=state.debug)
    stop_supervisor_daemon(debug=state.debug)
    reconfigure_supervisor(debug=state.debug)
    start_supervisor_daemon(debug=state.debug)


@main.command(help='Stop Oort processes.')
@basic_options
@pass_state
def stop(state):
    stop_supervisor_processes(debug=state.debug)


@main.command(help='Open web server in default browser')
@basic_options
@pass_state
def open(state):
    host = get_config_value('server', 'host')
    port = get_config_value('server', 'port')
    webbrowser.open(f"http://{host}:{port}")


@main.command(help='Tail the Oort logs.')
@click.option('-n', required=False, nargs=1, type=click.INT, help="The number of (last) lines to show (Default: 10).")
@basic_options
@pass_state
def logs(state, n):
    with builtins.open(get_log_file_path(), 'r') as f:
        print(''.join(tail(f, n or 10)))


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
              help="A customized astronomer to upload on behalf. You MUST provide")
@basic_options
@pass_state
def watch(state, folders, o=None, organisation=None, t=None, telescope=None, astronomer=None):
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
    telescope_uuid = t or telescope or ''
    telescope_details = None

    org_subdomain = o or organisation or ''
    org_role = ''
    username = ''
    api_key = ''

    # No custom astronomer. We MAY use an organisation. Let's check.
    if astronomer == (None, None):
        username = check_username(state.debug)

        if org_subdomain:
            check_organisation(org_subdomain, state.debug)
            org_role = check_organisation_local_membership(org_subdomain, state.debug)

        if org_subdomain and not telescope_uuid:
            list_organisation_telescopes(org_subdomain, state.debug)
            return

    else:
        if org_subdomain:
            click.echo("Error: if a custom astronomer is provided, no organisation can be used.")
            return

        username, api_key = astronomer
        check_astronomer_credentials(username, api_key, state.debug)
        if org_subdomain:
            check_astronomer_org_membership(org_subdomain, username, api_key, state.debug)

    # In every case, check for telescope details if a UUID is provided.
    if telescope_uuid:
        telescope_details = check_organisation_telescope(telescope_uuid, org_subdomain, api_key, state.debug)

    click.echo(" --- Folder(s) watch summary --- ")
    click.echo(f" • Account username: @{username}")
    if org_subdomain:
        click.echo(f" • Uploading for organisation: {org_subdomain} (role: {org_role})")
    else:
        click.echo(" • Uploading in *personal* account (use option '-o <subdomain>' for an organisation).")

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
                                               api_key,
                                               org_subdomain,
                                               org_role,
                                               telescope_details,
                                               state.debug)

        for (folder_path, identity) in prepared_folders:
            script_path = os.path.join(oort_folder, 'uploader', 'engine', 'initial_walk.py')
            subprocess.Popen(["python3", script_path, folder_path, identity.get_args_string()], close_fds=True)
            paths_observer.observe_folder(folder_path, identity)


@main.command(help="Get a list of all watched folders and their options.")
@basic_options
@pass_state
def list(state):
    for index, section in enumerate(get_config_upload_folder_sections()):
        click.echo(f" • Folder #{index + 1}:")
        click.echo(f"   username     = {section.get('username')}")
        click.echo(f"   api_key      = {section.get('api_key')[0:4]}•••••••")
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
