from oort.shared.errors import OortCloudError


class NotLoggedInOortCloudError(OortCloudError):
    def __init__(self):
        super().__init__('You must login first: `arcsecond login`')


class UnknownTelescopeOortCloudError(OortCloudError):
    def __init__(self, telescope_uuid):
        msg = f'Invalid / unknown telescopw with UUID {telescope_uuid}'
        super().__init__(msg)


class InvalidOrgMembershipOortCloudError(OortCloudError):
    def __init__(self, organisation):
        msg = f'Invalid / unknown membership for {organisation}. Login again: `arcsecond login --organisation {organisation}`'
        super().__init__(msg)


class InvalidOrganisationTelescopeOortCloudError(OortCloudError):
    def __init__(self, telescope_uuid):
        msg = f'Invalid / unknown telescope with UUID {telescope_uuid}.'
        super().__init__(msg)
