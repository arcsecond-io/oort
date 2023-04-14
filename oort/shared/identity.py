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
                 telescope_uuid: str = '',
                 zip: bool = False,
                 api: str = 'main'):
        assert username is not None
        assert upload_key is not None
        assert subdomain is not None
        assert role is not None
        assert upload_key is not None
        assert telescope_uuid is not None
        assert api is not None
        self._username = username
        self._upload_key = upload_key
        self._subdomain = subdomain or ''
        self._role = role or ''
        self._telescope_uuid = telescope_uuid or ''
        self._telescope_details = None
        self._zip = zip
        self._api = api

    # In python3, this will do the __ne__ by inverting the value
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Identity):
            return NotImplemented
        return self.username == other.username and self.upload_key == other.upload_key and \
            self.subdomain == other.subdomain and self.role == other.role and \
            self.telescope_uuid == other.telescope_uuid and self.zip == other.zip and self.api == other.api

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
    def telescope_uuid(self) -> str:
        return self._telescope_uuid

    @property
    def telescope_details(self) -> Optional[dict]:
        return self._telescope_details

    @property
    def zip(self) -> bool:
        return self._zip

    @property
    def api(self) -> str:
        return self._api

    def attach_telescope_details(self, **details):
        if 'uuid' not in details.keys() or \
                (self._telescope_uuid != '' and details.get('uuid') != self._telescope_uuid):
            raise ValueError('Wrong telescope UUID')
        if self._telescope_uuid == '':
            self._telescope_uuid = details.get('uuid')
        self._telescope_details = details

    def get_args_string(self):
        s = f"{self.username},{self.upload_key},{self.subdomain},{self.role},{self.telescope_uuid},"
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
                                         subdomain=self.subdomain,
                                         role=self.role,
                                         path=upload_folder_path,
                                         telescope=self.telescope_uuid,
                                         zip=str(self.zip),
                                         api=self.api)
