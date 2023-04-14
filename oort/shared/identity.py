import hashlib
import os
from typing import Optional

from oort.shared.config import write_oort_config_section_values


class Identity(object):
    @classmethod
    def from_folder_section(cls, folder_section):
        return cls(folder_section.get('username'),
                   folder_section.get('upload_key'),
                   folder_section.get('subdomain', ''),
                   folder_section.get('role', ''),
                   folder_section.get('telescope', ''),
                   folder_section.get('zip', 'False').lower() == 'true',
                   folder_section.get('api', ''))

    def __init__(self,
                 username: str,
                 upload_key: str,
                 subdomain: str = '',
                 role: str = '',
                 telescope: str = '',
                 zip: bool = False,
                 api: str = ''):
        self._username = username
        self._upload_key = upload_key
        self._subdomain = subdomain
        self._role = role
        self._telescope = telescope
        self._zip = zip
        self._api = api

    # In python3, this will do the __ne__ by inverting the value
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Identity):
            return NotImplemented
        return self.username == other.username and self.upload_key == other.upload_key and \
            self.subdomain == other.subdomain and self.role == other.role and \
            self.telescope == other.telescope and self.zip == other.zip and self.api == other.api

    @property
    def username(self) -> str:
        return self._username

    @property
    def upload_key(self) -> str:
        return self._upload_key

    @property
    def subdomain(self) -> str:
        return self._subdomain

    @property
    def role(self) -> str:
        return self._role

    @property
    def telescope(self) -> str:
        return self._telescope

    @property
    def zip(self) -> bool:
        return self._zip

    @property
    def api(self) -> str:
        return self._api

    def get_args_string(self):
        s = f"{self.username},{self.upload_key},{self.subdomain},{self.role},{self.telescope},"
        s += f"{str(self.zip)},{str(self.api)}"
        return s

    def save_with_folder(self, upload_folder_path: str):
        # If data are on disk that are attached, then detached and re-attached to a different volume
        # the full upload_folder_path will change, thus the folder_hash, and a new folder will be watched...
        folder_hash = hashlib.shake_128(upload_folder_path.encode('utf8')).hexdigest(3)
        suffix = '-tests' if os.environ.get('OORT_TESTS') == '1' else ''
        write_oort_config_section_values(f'watch-folder-{folder_hash}{suffix}',
                                         username=self.username,
                                         upload_key=self.upload_key,
                                         subdomain=self.subdomain or '',
                                         role=self.role or '',
                                         path=upload_folder_path,
                                         telescope=self.telescope or '',
                                         zip=str(self.zip),
                                         api=self.api)
