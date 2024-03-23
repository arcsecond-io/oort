import math
import pathlib

import click

from oort.common.identity import Identity
from oort.common.utils import is_file_hidden


def __get_formatted_time(seconds):
    if seconds > 86400:
        return f"{seconds / 86400:.1f}d"
    elif seconds > 3600:
        return f"{seconds / 3600:.1f}h"
    elif seconds > 60:
        return f"{seconds / 60:.1f}m"
    else:
        return f"{seconds:.1f}s"


def __get_formatted_size_times(size):
    total = f"{__get_formatted_time(size / pow(10, 4))} on 10 kB/s, "
    total += f"{__get_formatted_time(size / pow(10, 5))} on 100 kB/s, "
    total += f"{__get_formatted_time(size / pow(10, 6))} on 1 MB/s, "
    total += f"{__get_formatted_time(size / pow(10, 7))} on 10 MB/s"
    return total


def __get_formatted_bytes_size(size):
    if size == 0:
        return '0 Bytes'
    k = 1024
    units = ['Bytes', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    i = math.floor(math.log10(1.0 * size) / math.log10(k))
    return f"{(size / math.pow(k, i)):.2f} {units[i]}"


def display_command_summary(folders: list, identity: Identity):
    click.echo("\n --- Upload summary --- ")
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

    if identity.dataset_uuid:
        click.echo(f" • Ignoring folder names. Using a single dataset with name|uuid {identity.dataset_uuid}.")
    else:
        click.echo(" • Using folder names for dataset names (one folder = one dataset).")

    click.echo(f" • Folder{'s' if len(folders) > 1 else ''}:")
    for folder in folders:
        folder_path = pathlib.Path(folder).expanduser().resolve()
        click.echo(f"   > Path: {str(folder_path.parent if folder_path.is_file() else folder_path)}")

        if folder_path == pathlib.Path.home():
            click.echo("   >>> Warning: This folder is your HOME folder. <<<")

        size = sum(f.stat().st_size for f in folder_path.glob('**/*') if f.is_file() and not is_file_hidden(f))
        click.echo(f"   > Volume: {__get_formatted_bytes_size(size)} in total in this folder.")
        click.echo(f"   > Estimated upload time: {__get_formatted_size_times(size)}")
