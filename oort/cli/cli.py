import click
import webbrowser

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
from oort.config import get_config_value

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


@click.command(help=VERSION_HELP_STRING)
def version():
    click.echo(__version__)


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

# @main.command(short_help='Start oort server and uploads.')
# @click.option('-o', '--org', '--organisation', help="The subdomain of your organisation")
# @click.option('-t', '--tel', '--telescope', help="The UUID of the telescope acquiring data")
# @basic_options
# @pass_state
# def start(state, o=None, org=None, organisation=None, t=None, tel=None, telescope=None):
#     if not Arcsecond.is_logged_in():
#         raise NotLoggedInOortCloudError()
#
#     organisation = o or org or organisation
#     if organisation:
#         if state.verbose:
#             click.echo(f'Checking organisation {organisation} membership...')
#         if Arcsecond.memberships().get(organisation) is None:
#             raise InvalidOrgMembershipInOortCloudError(organisation)
#         if state.verbose:
#             click.echo('Checking telescopes API access...')
#         _, error = Arcsecond.build_telescopes_api(debug=state.debug, organisation=organisation).list()
#         if error:
#             raise OortCloudError(str(error))
#
#     # server_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'main.py')
#     # args = ['python3', server_path, os.getcwd(), organisation, str(state.debug), str(state.verbose)]
#     # subprocess.run([shlex_quote(arg) for arg in args], capture_output=True)
#
#     from .server import start
#
#     start(os.getcwd(), organisation, state.debug, state.verbose)
