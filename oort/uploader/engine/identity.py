class Identity(object):
    def __init__(self, username, api_key, organisation, telescope, debug=False):
        self._username = username
        self._api_key = api_key
        self._organisation = organisation
        self._telescope = telescope
        self._debug = debug

    @property
    def telescope(self):
        return self._telescope

    @property
    def organisation(self):
        return self._organisation

    @property
    def debug(self):
        return self._debug
