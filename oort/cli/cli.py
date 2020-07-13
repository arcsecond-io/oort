import click

from oort import __version__
from oort.cli.options import State, MethodChoiceParamType

pass_state = click.make_pass_decorator(State, ensure=True)

VERSION_HELP_STRING = "Show the Oort Cloud version and exit."
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help=VERSION_HELP_STRING)
@click.option('-V', is_flag=True, help=VERSION_HELP_STRING)
@click.option('-h', is_flag=True, help="Show this message and exit.")
@click.pass_context
def main(ctx, version=False, v=False, h=False):
    if version or v:
        click.echo(__version__)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command(help=VERSION_HELP_STRING)
def version():
    click.echo(__version__)


@main.command(help='Manage the local web server.')
@click.argument('method', required=False, nargs=1, type=MethodChoiceParamType(), default='status')
@pass_state
def server(state, method, **kwargs):
    pass


@main.command(help='Manage the uploader.')
@click.argument('method', required=False, nargs=1, type=MethodChoiceParamType(), default='status')
@pass_state
def uploader(state, method, **kwargs):
    pass

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
#     # server_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'server.py')
#     # args = ['python3', server_path, os.getcwd(), organisation, str(state.debug), str(state.verbose)]
#     # subprocess.run([shlex_quote(arg) for arg in args], capture_output=True)
#
#     from .server import start
#
#     start(os.getcwd(), organisation, state.debug, state.verbose)
