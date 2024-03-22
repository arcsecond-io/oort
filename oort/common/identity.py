from typing import Optional


class Identity(object):
    def __init__(self,
                 username: str,
                 upload_key: str,
                 organisation: Optional[dict] = None,
                 dataset: Optional[dict] = None,
                 api: str = 'main'):
        assert username is not None
        assert upload_key is not None
        assert upload_key is not None
        assert api is not None
        self._username = username
        self._upload_key = upload_key
        self._organisation = organisation or {}
        self._dataset = dataset or {}
        self._api = api

    # In python3, this will do the __ne__ by inverting the value
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Identity):
            return NotImplemented
        return self.username == other.username and self.upload_key == other.upload_key and \
            self.subdomain == other.subdomain and self.role == other.role and \
            self.dataset_uuid == other.dataset_uuid and self.api == other.api

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
    def dataset_uuid(self) -> str:
        return self._dataset.get('uuid', '')

    @property
    def dataset_name(self) -> str:
        return self._dataset.get('name', '')

    @property
    def api(self) -> str:
        return self._api

    @classmethod
    def from_folder_section(cls, folder_section):
        return cls(folder_section.get('username'),
                   folder_section.get('upload_key'),
                   {
                       'subdomain': folder_section.get('subdomain', ''),
                       'role': folder_section.get('role', '')
                   },
                   {
                       'uuid': folder_section.get('dataset_uuid', ''),
                       'name': folder_section.get('dataset_name', ''),
                   },
                   folder_section.get('api', ''))
