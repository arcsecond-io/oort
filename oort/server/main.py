#!/usr/bin/env python3

import socket

# sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from oort.config import get_logger
from oort.server.app import app
from oort.server.app.uploads import UploadsLocalState

logger = get_logger()


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def start(folder, organisation, debug, verbose):
    if verbose:
        print('Starting server...')

    app.config['folder'] = folder
    app.config['organisation'] = organisation
    app.config['debug'] = bool(debug)
    app.config['verbose'] = bool(verbose)
    app.config['upload_state'] = UploadsLocalState(app.config)

    port = 5000
    while is_port_in_use(port):
        port += 1

    logger.info('server start')
    app.run(debug=debug, host='0.0.0.0', port=port, threaded=True)


if __name__ == '__main__':
    print('Starting Server?')
    # start(*sys.argv[1:])
