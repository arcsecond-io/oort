import os
import pathlib
from typing import Optional

import click
from arcsecond import ArcsecondAPI

from oort.shared.config import (get_oort_config_upload_folder_sections, get_oort_logger)
from oort.shared.identity import Identity
from oort.shared.utils import get_formatted_bytes_size, get_formatted_size_times, is_hidden


def display_command_summary(folders: list, identity: Identity):
    click.echo(f"\n --- Upload/watch summary --- ")
    click.echo(f" • Arcsecond username: @{identity.username} (Upload key: {identity.upload_key[:4]}••••)")
    if identity.subdomain:
        msg = f" • Uploading to Observatory Portal '{identity.subdomain}' (as {identity.role})."
    else:
        msg = " • Uploading to your *personal* account."
    click.echo(msg)

    if identity.dataset_uuid and identity.dataset_name:
        msg = f" • Data will be appended to existing dataset '{identity.dataset_name}' ({identity.dataset_uuid})."
    elif not identity.dataset_uuid and identity.dataset_name:
        msg = f" • Data will be inserted into a new dataset named '{identity.dataset_name}'."
    else:
        msg = " • Using folder names for dataset names (one folder = one dataset)."
    click.echo(msg)

    if identity.telescope_uuid:
        msg = f" • Dataset(s) will be attached to telescope '{identity.telescope_name}' "
        if identity.telescope_alias:
            msg += f"a.k.a '{identity.telescope_alias}' "
        msg += f"({identity.telescope_uuid}))"
    else:
        msg = " • No designated telescope."
    click.echo(msg)

    click.echo(f" • Using API server: {identity.api}")
    click.echo(f" • Zip before upload: {'True' if zip else 'False'}")

    home_path = pathlib.Path.home()
    existing_folders = [section.get('path') for section in get_oort_config_upload_folder_sections()]

    click.echo(f" • Folder{'s' if len(folders) > 1 else ''}:")
    for folder in folders:
        folder_path = pathlib.Path(folder).expanduser().resolve()
        click.echo(f"   > Path: {str(folder_path.parent if folder_path.is_file() else folder_path)}")
        if folder_path == home_path:
            click.echo("   >>> Warning: This folder is your HOME folder. <<<")
        if str(folder_path) in existing_folders:
            click.echo("   >>> Warning: This folder is already watched. <<<")
        size = sum(f.stat().st_size for f in folder_path.glob('**/*') if f.is_file() and not is_hidden(f))
        click.echo(f"   > Volume: {get_formatted_bytes_size(size)} in total in this folder.")
        click.echo(f"   > Estimated upload time: {get_formatted_size_times(size)}")


def save_upload_folders(folders: list, identity: Identity) -> list:
    logger = get_oort_logger('cli', debug=identity.api == 'dev')

    prepared_folders = []
    for raw_folder in folders:
        upload_path = pathlib.Path(raw_folder).resolve()

        if not upload_path.exists() and os.environ.get('OORT_TESTS') != '1':
            logger.warning(f'Upload folder "{upload_path}" does not exists. Skipping.')
            continue

        if upload_path.is_file():
            upload_path = upload_path.parent

        identity.save_with_folder(upload_folder_path=str(upload_path))
        prepared_folders.append((str(upload_path), identity))

    return prepared_folders


def build_endpoint_kwargs(api: str = 'main', subdomain: Optional[str] = None):
    test = os.environ.get('OORT_TESTS') == '1'
    upload_key = ArcsecondAPI.upload_key(api=api)
    kwargs = {'test': test, 'api': api, 'upload_key': upload_key}
    if subdomain is not None:
        kwargs.update(organisation=subdomain)
    return kwargs
