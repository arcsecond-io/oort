import os
import socket
import click

from arcsecond import Arcsecond

from .app import app

from . import __version__
from .options import State, basic_options
from .errors import *


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


pass_state = click.make_pass_decorator(State, ensure=True)

VERSION_HELP_STRING = "Show the Oort Cloud version and exit."
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(invoke_without_command=True, context_settings=CONTEXT_SETTINGS)
@click.option('-v', '--version', is_flag=True, help=VERSION_HELP_STRING)
@click.option('-o', '--org', '--organisation', help="The subdomain of your organisation")
@click.option('-t', '--tel', '--telescope', help="The UUID of the telescope acquiring data")
@basic_options
@pass_state
@click.pass_context
def main(ctx, state, version=False, v=False, o=None, org=None, organisation=None, t=None, tel=None, telescope=None):
    if version or v:
        click.echo(__version__)

    elif ctx.invoked_subcommand is None:
        if not Arcsecond.is_logged_in():
            raise NotLoggedInOortCloudError()

        organisation = o or org or organisation
        if organisation:
            if Arcsecond.memberships().get(organisation) is None:
                raise InvalidOrgMembershipInOortCloudError(organisation)

        port = 5000
        while is_port_in_use(port):
            port += 1
        app.config['folder'] = os.getcwd()
        app.config['debug'] = state.debug
        app.config['organisation'] = organisation
        app.config['telescope'] = t or tel or telescope
        app.run(debug=state.debug, host='0.0.0.0', port=port, threaded=True)


@main.command(help=VERSION_HELP_STRING)
def version():
    click.echo(__version__)
