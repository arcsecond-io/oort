class OortCloudError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class NotLoggedInOortCloudError(OortCloudError):
    def __init__(self):
        super().__init__('You must login first: `arcsecond login`')


class InvalidOrgMembershipInOortCloudError(OortCloudError):
    def __init__(self, organisation):
        msg = f'Invalid / unknown membership for {organisation}. Login again: `arcsecond login --organisation {organisation}`'
        super().__init__(msg)
