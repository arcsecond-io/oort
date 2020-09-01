import hashlib
from typing import Optional

from arcsecond import ArcsecondAPI

from oort.shared.config import write_config_section_values


class Identity(object):
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

    def save_with_folder(self, upload_folder):
        folder_hash = hashlib.shake_128(upload_folder.encode('utf8')).hexdigest(3)
        write_config_section_values(f'watch-folder-{folder_hash}',
                                    username=ArcsecondAPI.username(),
                                    api_key=ArcsecondAPI.api_key(debug=self.debug),
                                    subdomain=self.subdomain or '',
                                    role=self.role or '',
                                    path=upload_folder,
                                    telescope=self.telescope or '',
                                    longitude=str(self._longitude) if self._longitude else '',
                                    debug=str(self.debug))
