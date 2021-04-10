import hashlib
import os
from typing import Optional

from oort.shared.config import write_config_section_values


class Identity(object):
    @classmethod
    def from_folder_section(cls, folder_section):
        return cls(folder_section.get('username'),
                   folder_section.get('api_key'),
                   folder_section.get('subdomain', ''),
                   folder_section.get('role', ''),
                   folder_section.get('telescope', ''),
                   folder_section.get('longitude', ''),
                   folder_section.get('debug', 'False').lower() == 'true')

    def __init__(self,
                 username: str,
                 api_key: str,
                 subdomain: Optional[str] = None,
                 role: Optional[str] = None,
                 telescope: Optional[str] = None,
                 longitude: Optional[float] = None,
                 debug: bool = False):
        self._username = username
        self._api_key = api_key
        self._subdomain = subdomain
        self._role = role
        self._telescope = telescope
        self._longitude = longitude
        self._debug = debug

    @property
    def username(self) -> str:
        return self._username

    @property
    def api_key(self) -> str:
        return self._api_key

    @property
    def subdomain(self) -> Optional[str]:
        return self._subdomain

    @property
    def role(self) -> Optional[str]:
        return self._role

    @property
    def telescope(self) -> Optional[str]:
        return self._telescope

    @property
    def longitude(self) -> Optional[float]:
        return self._longitude

    @property
    def debug(self) -> bool:
        return self._debug

    def get_args_string(self):
        return f"{self.username},{self.api_key},{self.subdomain},{self.role},{self.telescope},{self.longitude},{str(self.debug)}"

    def save_with_folder(self, upload_folder_path: str):
        folder_hash = hashlib.shake_128(upload_folder_path.encode('utf8')).hexdigest(3)
        suffix = '-tests' if os.environ.get('OORT_TESTS') == '1' else ''
        write_config_section_values(f'watch-folder-{folder_hash}{suffix}',
                                    username=self._username,
                                    api_key=self._api_key,
                                    subdomain=self.subdomain or '',
                                    role=self.role or '',
                                    path=upload_folder_path,
                                    telescope=self.telescope or '',
                                    longitude=str(self._longitude) if self._longitude else '',
                                    debug=str(self.debug))
