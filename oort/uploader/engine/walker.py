from pathlib import Path

import click

from oort.cli.folders import check_remote_organisation
from oort.shared.config import get_oort_logger
from oort.shared.identity import Identity
from oort.shared.models import Status
from oort.shared.utils import is_hidden
from oort.uploader.engine import packer

logger = get_oort_logger('walker')


def walk_first_pass(root_path: Path, identity: Identity, force: bool):
    log_prefix = '[Walker - 1/2]'
    logger.info(f"{log_prefix} Making a first pass to collect info on files...")

    total_file_count = sum(1 for f in root_path.glob('**/*') if f.is_file() and not is_hidden(f))

    index = 0
    unfinished_paths = []
    for file_path in root_path.glob('**/*'):
        # Skipping both hidden files and hidden directories.
        if is_hidden(file_path) or not file_path.is_file():
            continue

        index += 1
        click.echo(f"\n{log_prefix} File {index} / {total_file_count} ({index / total_file_count * 100:.2f}%)\n")

        pack = packer.UploadPack(str(root_path), str(file_path), identity, force=force)
        if not pack.is_already_finished or force:
            pack.collect_file_info()
            unfinished_paths.append(file_path)
        else:
            logger.info(f"{log_prefix} Upload of file {str(file_path)} already marked as finished.")

    logger.info(f"\n{log_prefix} Finished collecting file info inside folder {str(root_path)}.\n")
    return unfinished_paths


def walk_second_pass(root_path: Path, identity: Identity, unfinished_paths: list, force: bool):
    log_prefix = '[Walker - 2/2]'
    logger.info(f"{log_prefix} Starting second pass to upload files...")

    failed_uploads = []
    success_uploads = []
    total_file_count = len(unfinished_paths)

    index = 0
    for file_path in unfinished_paths:
        index += 1
        click.echo(f"\n{log_prefix} File {index} / {total_file_count} ({index / total_file_count * 100:.2f}%)\n")

        pack = packer.UploadPack(str(root_path), str(file_path), identity, force=force)
        status, substatus, error = pack.prepare_and_upload_file(display_progress=True)
        if status == Status.OK.value:
            success_uploads.append(str(file_path))
        else:
            failed_uploads.append((str(file_path), substatus, error))

    msg = f"{log_prefix}\n\n\nFinished upload walk inside folder {root_path} "
    logger.info(msg)

    return success_uploads, failed_uploads


def walk(folder_string: str, identity: Identity, force: bool, debug: bool):
    if identity.subdomain:
        check_remote_organisation(identity.subdomain, debug, verbose=False)

    log_prefix = '[Walker]'
    root_path = Path(folder_string).resolve()
    if root_path.is_file():  # Just in case we pass a file...
        root_path = root_path.parent

    logger.info(f"{log_prefix} Starting upload walk through {root_path} and its subfolders...")
    if force:
        logger.warn(f"{log_prefix} Force flag is {'True' if force else 'False'}")

    unfinished_paths = walk_first_pass(root_path, identity, force)
    if len(unfinished_paths) > 0:
        success_uploads, failed_uploads = walk_second_pass(root_path, identity, unfinished_paths, force)
        msg = f"{log_prefix} {len(success_uploads)} successful uploads and {len(failed_uploads)} failed.\n\n"
        logger.info(msg)

        if len(failed_uploads) > 0:
            logger.error(f'{log_prefix} Here are the failed uploads:')
            for path, substatus, error in failed_uploads:
                logger.error(f'{path} ({substatus}) {error}')
    else:
        msg = f"{log_prefix} No new file paths to upload.\n\n"
        logger.info(msg)

# if __name__ == '__main__':
#     root_path = sys.argv[1]
#     username, upload_key, subdomain, role, telescope, debug_str = sys.argv[2].split(",")
#     debug = (debug_str == 'True')
#     identity = Identity(username, upload_key, subdomain, role, telescope, debug)
#     walk(root_path, identity, debug)
