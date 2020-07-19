#!/usr/bin/env python3

import socket
import os
import sys

from oort.config import get_logger, write_config_value
from oort.server.app import app
from oort.server.app.uploads import UploadsLocalState


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def start(debug=False):
    logger = get_logger(debug=debug)

    app.config['folder'] = os.getcwd()
    app.config['debug'] = bool(debug)
    app.config['verbose'] = False
    app.config['organisation'] = None
    app.config['upload_state'] = UploadsLocalState(app.config)

    host = '0.0.0.0'
    port = 5000
    while is_port_in_use(port):
        port += 1

    # write_config_value('server', 'host', host)
    # write_config_value('server', 'port', str(port))

    logger.info(f'Starting Oort web server (http://{host}:{port}) ...')
    app.run(debug=debug, host=host, port=port)

if __name__ == '__main__':
    debug = len(sys.argv) > 1 and sys.argv[1] in ['-d', '--debug']
    start(debug)
