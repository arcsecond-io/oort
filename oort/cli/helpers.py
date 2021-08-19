import pathlib

import click

from oort.shared.config import (get_oort_config_upload_folder_sections)
from oort.shared.utils import get_formatted_bytes_size, get_formatted_size_times, is_hidden


def display_command_summary(folders, username, upload_key, org_subdomain, org_role, telescope_details, zip):
    click.echo(f"\n --- Folder{'s' if len(folders) > 1 else ''} summary --- ")
    click.echo(f" • Arcsecond username: @{username} (Upload key: {upload_key[:4]}••••)")
    if not org_subdomain:
        click.echo(" • Uploading to your *personal* account.")
    else:
        click.echo(f" • Uploading to organisation account '{org_subdomain}' (as {org_role}).")

    if telescope_details:
        msg = f" • Datasets will be tagged with telescope '{telescope_details.get('name')}' "
        if telescope_details.get('alias', ''):
            msg += f"alias \"{telescope_details.get('alias')}\" "
        msg += f"({telescope_details.get('uuid')}))"
        click.echo(msg)
    else:
        click.echo(" • No designated telescope.")

    click.echo(f" • Zip datafiles: {'True' if zip else 'False'}")

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
        click.echo(f"   > Estimated time: {get_formatted_size_times(size)}")
