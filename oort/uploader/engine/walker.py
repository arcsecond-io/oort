from pathlib import Path

import click

from oort.cli.folders import check_remote_organisation
from oort.shared.config import get_oort_logger
from oort.shared.identity import Identity
from oort.shared.models import Status
from oort.shared.utils import is_hidden
from oort.uploader.engine import packer


def walk(folder_path: str, identity: Identity, force, debug: bool):
    if identity.subdomain:
        check_remote_organisation(identity.subdomain, debug, verbose=False)

    log_prefix = '[Walker]'
    logger = get_oort_logger('walker', debug=debug)
    logger.info(f"{log_prefix} Starting upload walk through {folder_path} and its subfolders...")
    logger.warn(f"{log_prefix} Force flag is {'True' if force else 'False'}")

    root_path = Path(folder_path)
    # Just in case we pass a file...
    if root_path.is_file():
        root_path = root_path.parent

    failed_uploads = []
    success_uploads = []

    index = 0
    total_count = sum(1 for f in root_path.glob('**/*') if f.is_file() and not is_hidden(f))
    for file_path in root_path.glob('**/*'):
        # Skipping both hidden files and hidden directories.
        if is_hidden(file_path) or not file_path.is_file():
            continue

        index += 1
        click.echo(f"\n{log_prefix} File {index} / {total_count} ({index / total_count * 100:.2f}%)\n")

        pack = packer.UploadPack(str(root_path), str(file_path), identity, force=force)
        status, substatus, error = pack.prepare_and_upload_file(display_progress=True)
        if status == Status.OK.value:
            success_uploads.append(str(file_path))
        else:
            failed_uploads.append((str(file_path), substatus, error))

    msg = f'{log_prefix} Finished upload walk inside folder {folder_path} '
    msg += f'with {len(success_uploads)} successful uploads and {len(failed_uploads)} failed.'
    logger.info(msg)

    if len(failed_uploads) > 0:
        logger.error(f'{log_prefix} Here are the failed uploads:')
        for path, substatus, error in failed_uploads:
            logger.error(f'{path} ({substatus}) {error}')

# if __name__ == '__main__':
#     root_path = sys.argv[1]
#     username, upload_key, subdomain, role, telescope, debug_str = sys.argv[2].split(",")
#     debug = (debug_str == 'True')
#     identity = Identity(username, upload_key, subdomain, role, telescope, debug)
#     walk(root_path, identity, debug)
