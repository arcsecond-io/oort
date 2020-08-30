import builtins
import os
import webbrowser

import click
from arcsecond import ArcsecondAPI

from oort import __version__
from oort.cli.folders import (check_organisation, check_organisation_membership, check_organisation_telescope,
                              save_upload_folders)
from oort.cli.options import State, basic_options
from oort.cli.supervisor import (configure_supervisor, get_supervisor_processes_status, restart_supervisor_processes,
                                 start_supervisor_daemon)
from oort.shared.config import get_config_value, get_log_file_path
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
    Oort-Cloud ('oort' command) is a super-easy upload manager for arcsecond.io

    It monitors folders you indicates, and upload all files contained in the
    folder (and its subfolders), *using the folder structure to infer the
    organisation of files*.

    For instance, if a folder contains the word "Bias" (case-insensitive), the
    files inside it will be put inside a Calibration object, associated with
    a Dataset whose name is that of the folder.

    Special names directing files in Calibrations are "Bias", "Dark", "Flat" and
    "Calib". All other folder names are considered as target names, and put
    inside Observations.

    All Calibrations and Observations are automatically  associated with
    Night Logs whose date is inferred from the observation date of the files.
    Oort takes automatically care of the right "date" whether the file is taken
    before or after noon on that local place. In other words, the "night"
    boundaries are running from local noon to the next local noon.

    Oort-Cloud works by managing 2 processes:\n
    • An uploader, which takes care of creating/syncing the right Night Logs,
        Datasets and Datafiles in Arcsecond.io (either in your personal account,
        or your Organisation). And then upload the files.\n
    • A small web server, which allow you to monitor, control and setup what is
        happening in the uploader (and find what happened before too).

    The `oort` command is dedicated to start, stop and get status
    of these two processes. Once they are up and running, only ONE thing
    remain to be done by you: indicate which folders `oort` should monitor
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
    """Login to your personal Arcsecond.io account, and retrieve the associated API key.
    This API key is a secret token you should take care. It will be stored locally on a file:
    ~/.arcsecond.ini

    Make sure to indicate the organisation subdomain if you intend to upload for that
    organisation.
    """
    ArcsecondAPI.login(username, password, None, debug=state.debug)


#
# @main.command(help='Start Oort processes.')
# @basic_options
# @pass_state
# def start(state):
#     start_supervisor_processes(debug=state.debug)
#
#
# @main.command(help='Stop Oort processes.')
# @basic_options
# @pass_state
# def stop(state):
#     stop_supervisor_processes(debug=state.debug)
#
#
# @main.command(help='Restart Oort processes.')
# @basic_options
# @pass_state
# def restart(state):
#     restart_supervisor_processes(debug=state.debug)
#

@main.command(help='Get Oort processes status.')
@basic_options
@pass_state
def status(state):
    get_supervisor_processes_status(debug=state.debug)


@main.command(help='Reload and restart Oort.')
@basic_options
@pass_state
def reload(state):
    configure_supervisor(debug=state.debug)
    start_supervisor_daemon(debug=state.debug)
    restart_supervisor_processes(debug=state.debug)


@main.command(help='Open web server in default browser')
@basic_options
@pass_state
def open(state):
    host = get_config_value('server', 'host')
    port = get_config_value('server', 'port')
    webbrowser.open(f"http://{host}:{port}")


@main.command(help='Tail the logs.')
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
@basic_options
@pass_state
def watch(state, folders, o=None, organisation=None, t=None, telescope=None):
    """
    Indicate a folder (or multiple folders) that oort should monitor for files
    to upload.

    Oort will walk through the folder tree and uploads files according to the
    name of the subfolders (see main help).
    """
    telescope_uuid = t or telescope or ''
    org_subdomain = o or organisation or ''

    if org_subdomain:
        check_organisation(org_subdomain, state.debug)

    telescope_details = check_organisation_telescope(org_subdomain, telescope_uuid, state.debug)
    org_role = check_organisation_membership(org_subdomain, state.debug)

    click.echo(" --- Folder(s) watch summary --- ")
    click.echo(f" • Account username: @{ArcsecondAPI.username(debug=state.debug)}")
    if org_subdomain:
        click.echo(f" • Uploading for organisation: {org_subdomain} (role: {org_role})")
    else:
        click.echo(" • Uploading in *personal* account.")

    if telescope_details:
        name, uuid = telescope_details.get('name'), telescope_details.get('uuid')
        click.echo(f" • Night Logs will be linked to telescope '{name}' ({uuid}).")
    else:
        click.echo(" • No designated telescope.")

    click.echo(" • Dates inside FITS/XISF files are assumed to be local dates.")

    if len(folders) == 1:
        click.echo(f" • Folder: {os.path.expanduser(os.path.realpath(folders[0]))}")
    else:
        click.echo(" • Folders:")
        for folder in folders:
            click.echo(f"   - {os.path.expanduser(os.path.realpath(folder))}")

    ok = input(' --> OK? (Press Enter) ')

    if ok.strip() == '':
        prepared_folders = save_upload_folders(folders, org_subdomain, org_role, telescope_details, state.debug)
        for (upload_folder, identity) in prepared_folders:
            paths_observer.observe_folder(upload_folder, identity)
