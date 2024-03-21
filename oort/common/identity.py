import hashlib
import os
from typing import Optional

from .config import write_oort_config_section_values


class Identity(object):
    def __init__(self,
                 username: str,
                 upload_key: str,
                 organisation: Optional[dict] = None,
                 telescope: Optional[dict] = None,
                 dataset: Optional[dict] = None,
                 zip: bool = False,
                 api: str = 'main'):
        assert username is not None
        assert upload_key is not None
        assert upload_key is not None
        assert api is not None
        self._username = username
        self._upload_key = upload_key
        self._organisation = organisation or {}
        self._telescope = telescope or {}
        self._dataset = dataset or {}
        self._telescope_details = None
        self._zip = zip
        self._api = api

    # In python3, this will do the __ne__ by inverting the value
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Identity):
            return NotImplemented
        return self.username == other.username and self.upload_key == other.upload_key and \
            self.subdomain == other.subdomain and self.role == other.role and \
            self.telescope_uuid == other.telescope_uuid and self.zip == other.zip \
            and self.dataset_uuid == other.dataset_uuid and self.api == other.api

    @property
    def username(self) -> str:
        return self._username

    @property
    def upload_key(self) -> str:
        return self._upload_key

    @property
    def subdomain(self) -> str:
        return self._organisation.get('subdomain', '')

    @property
    def role(self) -> str:
        return self._organisation.get('role', '')

    @property
    def telescope_uuid(self) -> str:
        return self._telescope.get('uuid', '')

    @property
    def telescope_name(self) -> str:
        return self._telescope.get('name', '')

    @property
    def telescope_alias(self) -> str:
        return self._telescope.get('alias', '')

    @property
    def dataset_uuid(self) -> str:
        return self._dataset.get('uuid', '')

    @property
    def dataset_name(self) -> str:
        return self._dataset.get('name', '')

    @property
    def zip(self) -> bool:
        return self._zip

    @property
    def api(self) -> str:
        return self._api

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
                                         telescope_uuid=self.telescope_uuid,
                                         telescope_name=self.telescope_name,
                                         telescope_alias=self.telescope_alias,
                                         dataset_uuid=self.dataset_uuid,
                                         dataset_name=self.dataset_name,
                                         zip=str(self.zip),
                                         api=self.api)

    @classmethod
    def from_folder_section(cls, folder_section):
        return cls(folder_section.get('username'),
                   folder_section.get('upload_key'),
                   {
                       'subdomain': folder_section.get('subdomain', ''),
                       'role': folder_section.get('role', '')
                   },
                   {
                       'uuid': folder_section.get('telescope_uuid', ''),
                       'name': folder_section.get('telescope_name', ''),
                       'alias': folder_section.get('telescope_alias', '')
                   },
                   {
                       'uuid': folder_section.get('dataset_uuid', ''),
                       'name': folder_section.get('dataset_name', ''),
                   },
                   folder_section.get('zip', 'False').lower() == 'true',
                   folder_section.get('api', ''))
