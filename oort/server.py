import os
import socket
import click

from .app import app
from .app.models import db
from .app.views import *

from . import __version__
from .options import State, basic_options


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


pass_state = click.make_pass_decorator(State, ensure=True)

VERSION_HELP_STRING = "Show the Oort Cloud version and exit."
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(invoke_without_command=True, context_settings=CONTEXT_SETTINGS)
@click.option('-v', '--version', is_flag=True, help=VERSION_HELP_STRING)
@basic_options
@pass_state
@click.pass_context
def main(ctx, state, version=False, v=False):
    if version or v:
        click.echo(__version__)
    elif ctx.invoked_subcommand is None:
        db.bind(**app.config['PONY'])
        db.generate_mapping(create_tables=True)
        port = 5000
        while is_port_in_use(port):
            port += 1
        app.config['folder'] = os.getcwd()
        app.config['debug'] = state.debug
        app.run(debug=state.debug, port=port)
