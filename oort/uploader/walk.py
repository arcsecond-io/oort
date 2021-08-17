import os
import sys
import time

from oort.cli.folders import check_remote_organisation
from oort.shared.config import get_oort_logger
from oort.shared.identity import Identity
from oort.uploader.engine import packer


def perform_walk(root_path: str, identity: Identity, debug: bool):
    logger = get_oort_logger('walker', debug=debug)
    logger.info(f'Running walk for {root_path}')

    if identity.subdomain:
        check_remote_organisation(identity.subdomain, debug, verbose=False)

    time.sleep(0.2)

    for root, _, filenames in os.walk(root_path):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            if os.path.isfile(file_path) and not os.path.basename(file_path).startswith('.'):
                pack = packer.UploadPack(root_path, file_path, identity)
                pack.prepare_and_upload_file()

    logger.info(f'Finished initial walk for {root_path}')


if __name__ == '__main__':
    root_path = sys.argv[1]
    username, upload_key, subdomain, role, telescope, debug_str = sys.argv[2].split(",")
    debug = (debug_str == 'True')
    identity = Identity(username, upload_key, subdomain, role, telescope, debug)
    perform_walk(root_path, identity, debug)
