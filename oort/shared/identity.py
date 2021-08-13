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
                   folder_section.get('longitude', ''),
                   folder_section.get('zip', 'False').lower() == 'true',
                   folder_section.get('debug', 'False').lower() == 'true')

    def __init__(self,
                 username: str,
                 upload_key: str,
                 subdomain: Optional[str] = None,
                 role: Optional[str] = None,
                 telescope: Optional[str] = None,
                 longitude: Optional[float] = None,
                 zip: bool = False,
                 debug: bool = False):
        self._username = username
        self._upload_key = upload_key
        self._subdomain = subdomain
        self._role = role
        self._telescope = telescope
        self._longitude = longitude
        self._zip = zip
        self._debug = debug

    @property
    def username(self) -> str:
        return self._username

    @property
    def upload_key(self) -> str:
        return self._upload_key

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
    def zip(self) -> bool:
        return self._zip

    @property
    def debug(self) -> bool:
        return self._debug

    def get_args_string(self):
        s = f"{self.username},{self.upload_key},{self.subdomain},{self.role},{self.telescope},{self.longitude},"
        s += f"{str(self.zip)},{str(self.debug)}"
        return s

    def save_with_folder(self, upload_folder_path: str):
        folder_hash = hashlib.shake_128(upload_folder_path.encode('utf8')).hexdigest(3)
        suffix = '-tests' if os.environ.get('OORT_TESTS') == '1' else ''
        write_oort_config_section_values(f'watch-folder-{folder_hash}{suffix}',
                                         username=self.username,
                                         upload_key=self.upload_key,
                                         subdomain=self.subdomain or '',
                                         role=self.role or '',
                                         path=upload_folder_path,
                                         telescope=self.telescope or '',
                                         longitude=str(self.longitude) if self.longitude else '',
                                         zip=str(self.zip),
                                         debug=str(self.debug))
