import webbrowser

import click
from arcsecond import ArcsecondAPI

from oort import __version__
from oort.cli.folders import save_upload_folders
from oort.cli.options import State, basic_options
from oort.cli.supervisor import (configure_supervisor, get_supervisor_processes_status, restart_supervisor_processes,
                                 start_supervisor_daemon, start_supervisor_processes, stop_supervisor_processes)
from oort.shared.config import get_config_value
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

    Special names directing files in Calibrations are "Bias", "Dark" and "Flat".
    Subfolders of "Flat" will be considered as filter names. All other folder
    names are considered as target names, and put inside Observation objects.

    All Calibrations and Observations are automatically  associated with
    Night Logs whose date is inferred from the observation date of the files.
    Oort takes automatically care of the right "date" whether the file is taken
    before or after midnight on that local place.

    It does so by knowing the Telescope. If no telescope could be found, the
    date is taken at face value.

    Oort-Cloud works by managing 2 processes:\n
    • An uploader, which takes care of creating/syncing the right Night Logs,
        Datasets and Datafiles in Arcsecond.io (either in your personal account,
        or your Organisation). And then upload the files.\n
    • A small web server, which allow you to monitor, control and setup what is
        happening in the uploader (and find what happened before too).

    The `oort` command is dedicated to starting, stopping and getting status
    of these two processes. Once they are up and running, only ONE thing
    remain to be done by you: indicate which folders `oort` should monitor
    to find files to upload.
    """
    if version:
        click.echo(__version__)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.option('-u', '--username', required=True, nargs=1, prompt=True)
@click.option('-p', '--password', required=True, nargs=1, prompt=True, hide_input=True)
@click.option('-o', '--organisation', required=False, help='organisation subdomain')
@basic_options
@pass_state
def login(state, u, username, p, password, o=None, organisation=None):
    """Login to your personal Arcsecond.io account, and retrieve the associated API key.
    This API key is a secret token you should take care. It will be stored locally on a file:
    ~/.arcsecond.ini

    Make sure to indicate the organisation subdomain if you intend to upload for that
    organisation.
    """
    ArcsecondAPI.login(u or username, p or password, o or organisation, state)


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


@main.command(help='Restart Oort processes.')
@basic_options
@pass_state
def restart(state):
    restart_supervisor_processes(debug=state.debug)


@main.command(help='Get Oort processes status.')
@basic_options
@pass_state
def status(state):
    get_supervisor_processes_status(debug=state.debug)


@main.command(help='Reload Oort configuration (for enabling/disabling debug).')
@basic_options
@pass_state
def reload(state):
    configure_supervisor(debug=state.debug)
    start_supervisor_daemon(debug=state.debug)


@main.command(help='Open web server in default browser')
@basic_options
@pass_state
def open(state):
    host = get_config_value('server', 'host')
    port = get_config_value('server', 'port')
    webbrowser.open(f"http://{host}:{port}")


@main.command()
@click.argument('folders', required=True, nargs=-1)
@click.option('-t', '--tel', '--telescope',
              required=False,
              nargs=1,
              type=click.UUID,
              help="The UUID of the telescope acquiring data (in the case of organisation uploads).")
@pass_state
def upload(state, folders, t=None, tel=None, telescope=None):
    """
    Indicate a folder (or multiple folders) that oort should monitor for files
    to upload.

    Oort will walk through the folder tree and uploads file according to the
    name of the subfolders.

    If no folder is provided, the current one is selected.
    """
    telescope_uuid = t or tel or telescope
    prepared_folders = save_upload_folders(folders, telescope_uuid, state.debug)

    for (upload_folder, identity) in prepared_folders:
        paths_observer.start_observe_folder(upload_folder, identity)
