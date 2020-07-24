class Identity(object):
    def __init__(self, username, organisation, role, telescope, debug=False):
        self._username = username
        self._organisation = organisation
        self._role = role
        self._telescope = telescope
        self._debug = debug

    @property
    def username(self):
        return self._username

    @property
    def organisation(self):
        return self._organisation

    @property
    def role(self):
        return self._role

    @property
    def telescope(self):
        return self._telescope

    @property
    def debug(self):
        return self._debug
