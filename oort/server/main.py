#!/usr/bin/env python3

import socket
import os
import sys

from oort.shared.config import get_logger, write_config_value
from oort.server.app import app
from oort.server.app.context import Context


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def start(debug=False):
    logger = get_logger(debug=debug)

    app.config['folder'] = os.getcwd()
    app.config['debug'] = bool(debug)
    app.config['verbose'] = False
    app.config['organisation'] = None
    app.config['context'] = Context(app.config)

    host = '0.0.0.0'
    port = 5000
    while is_port_in_use(port):
        port += 1

    if debug is False:
        # In debug, Werkzeug start 2 servers, provoking the saving of a wrong port value.
        write_config_value('server', 'host', host)
        write_config_value('server', 'port', str(port))

    d = 'debug ' if debug else ' '
    logger.info(f'Starting Oort {d}web server (http://{host}:{port})...')
    app.run(debug=debug, host=host, port=port)


if __name__ == '__main__':
    debug = len(sys.argv) > 1 and sys.argv[1] in ['-d', '--debug']
    start(debug)
