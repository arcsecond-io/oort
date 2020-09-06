from oort.shared.errors import OortCloudError


class NotLoggedInOortCloudError(OortCloudError):
    def __init__(self):
        super().__init__('You must login first: `arcsecond login`')


class UnknownOrganisationOortCloudError(OortCloudError):
    def __init__(self, subdomain, error_string):
        msg = f'Invalid / unknown organisation with subdomain {subdomain}: {error_string}'
        super().__init__(msg)


class UnknownTelescopeOortCloudError(OortCloudError):
    def __init__(self, telescope_uuid):
        msg = f'Invalid / unknown telescope with UUID {telescope_uuid}'
        super().__init__(msg)


class InvalidAstronomerOortCloudError(OortCloudError):
    def __init__(self, username, api_key):
        msg = f'Invalid / unknown astronomer with username {username} (for the provided api_key {api_key}). '
        super().__init__(msg)


class InvalidOrgMembershipOortCloudError(OortCloudError):
    def __init__(self, subdomain):
        msg = f'Invalid / unknown membership for {subdomain}.'
        super().__init__(msg)


class InvalidOrganisationTelescopeOortCloudError(OortCloudError):
    def __init__(self, telescope_uuid):
        msg = f'Invalid / unknown telescope with UUID {telescope_uuid}.'
        super().__init__(msg)
