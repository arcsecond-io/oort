from typing import Optional


class Identity(object):
    def __init__(self,
                 username: str,
                 api_key: str,
                 organisation: Optional[str] = None,
                 role: Optional[str] = None,
                 telescope: Optional[str] = None,
                 debug: bool = False):
        self._username = username
        self._api_key = api_key
        self._organisation = organisation
        self._role = role
        self._telescope = telescope
        self._debug = debug

    @property
    def username(self) -> str:
        return self._username

    @property
    def api_key(self) -> str:
        return self._api_key

    @property
    def organisation(self) -> Optional[str]:
        return self._organisation

    @property
    def role(self) -> Optional[str]:
        return self._role

    @property
    def telescope(self) -> Optional[str]:
        return self._telescope

    @property
    def debug(self) -> bool:
        return self._debug
