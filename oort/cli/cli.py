import os
import hashlib

import click
import webbrowser

from arcsecond import Arcsecond

from oort import __version__
from oort.cli.options import State, basic_options
from oort.cli.supervisor import (
    configure_supervisor,
    start_supervisor_daemon,
    start_supervisor_processes,
    stop_supervisor_processes,
    restart_supervisor_processes,
    get_supervisor_processes_status
)
from oort.shared.config import get_config_value, write_config_section_values
from oort.server.app.helpers.utils import look_for_telescope_uuid
from oort.server.errors import InvalidOrganisationTelescopeOortCloudError, NotLoggedInOortCloudError

pass_state = click.make_pass_decorator(State, ensure=True)

VERSION_HELP_STRING = "Show the Oort Cloud version and exit."
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help=VERSION_HELP_STRING)
@basic_options
@click.pass_context
def main(ctx, version=False, **kwargs):
    if version:
        click.echo(__version__)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command(help='Login to Arcsecond.io (Oort Mothership).')
@click.option('-u', '--username', required=True, nargs=1, prompt=True)
@click.option('-p', '--password', required=True, nargs=1, prompt=True, hide_input=True)
@click.option('-o', '--organisation', required=False, help='organisation subdomain')
@basic_options
@pass_state
def login(state, u, username, p, password, o=None, organisation=None):
    """Login to your personal Arcsecond.io account, and retrieve the associated API key."""
    Arcsecond.login(u or username, p or password, o or organisation, state)


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


@main.command(help='Select a root folder to upload.')
@click.argument('folder', required=True, nargs=-1)
@click.option('-t', '--tel', '--telescope',
              required=False, nargs=1,
              help="The UUID of the telescope acquiring data (in the case of organisation uploads).")
@pass_state
def upload(state, folder, t=None, tel=None, telescope=None):
    """
    Oort will walk through the folder tree and uploads file according to the
    name of the subfolders.

    If no folder is provided, the current one is selected. Multiple
    folder can also be provided, separated by a white space.
    """
    if not Arcsecond.is_logged_in():
        raise NotLoggedInOortCloudError()

    telescope_uuid = t or tel or telescope
    role, organisation, telescope_name = None, None, None

    if telescope_uuid is not None:
        memberships = Arcsecond.memberships()
        for org_subdomain, membership_role in memberships.items():
            api = Arcsecond.build_telescopes_api(debug=state.debug, organisation=org_subdomain)
            telescope_data, error = api.read(telescope_uuid)
            if error is None:
                telescope_name = telescope_data.get('name')
                organisation = org_subdomain
                role = membership_role
                break
        if organisation is None:
            raise InvalidOrganisationTelescopeOortCloudError('')

    for raw_folder in folder:
        upload_folder = os.path.expanduser(os.path.realpath(raw_folder))
        legacy_telescope_uuid = look_for_telescope_uuid(upload_folder)

        if telescope_uuid and legacy_telescope_uuid and telescope_uuid != legacy_telescope_uuid:
            raise InvalidOrganisationTelescopeOortCloudError(legacy_telescope_uuid)

        final_telescope_uuid = telescope_uuid or legacy_telescope_uuid
        folder_hash = hashlib.shake_128(upload_folder.encode('utf8')).hexdigest(3)

        write_config_section_values(f'upload-folder-{folder_hash}',
                                    username=Arcsecond.username(),
                                    organisation=organisation or '',
                                    role=role or '',
                                    path=upload_folder,
                                    telescope_uuid=final_telescope_uuid or '',
                                    telescope_name=telescope_name or '',
                                    status='pending')
