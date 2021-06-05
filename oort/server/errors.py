from oort.shared.errors import OortCloudError


class NotLoggedInOortCloudError(OortCloudError):
    def __init__(self):
        super().__init__('You must login first: `oort login`')


class InvalidWatchOptionsOortCloudError(OortCloudError):
    def __init__(self, msg=''):
        super().__init__(f'Invalid or incomplete Watch options: {msg}')


class UnknownOrganisationOortCloudError(OortCloudError):
    def __init__(self, subdomain, error_string):
        msg = f'Invalid / unknown organisation with subdomain {subdomain}: {error_string}'
        super().__init__(msg)


class UnknownTelescopeOortCloudError(OortCloudError):
    def __init__(self, telescope_uuid):
        msg = f'Invalid / unknown telescope with UUID {telescope_uuid}'
        super().__init__(msg)


class InvalidAstronomerOortCloudError(OortCloudError):
    def __init__(self, username, upload_key=None):
        msg = f'Invalid / unknown astronomer with username "{username}"'
        if upload_key:
            msg += f' (for the provided upload_key "{upload_key}")'
        super().__init__(msg)


class InvalidOrgMembershipOortCloudError(OortCloudError):
    def __init__(self, subdomain):
        msg = f'Invalid / unknown membership for {subdomain}.'
        super().__init__(msg)


class InvalidOrganisationTelescopeOortCloudError(OortCloudError):
    def __init__(self, telescope_uuid):
        msg = f'Invalid / unknown telescope with UUID {telescope_uuid}.'
        super().__init__(msg)


class InvalidOrganisationUploadKeyOortCloudError(OortCloudError):
    def __init__(self, subdomain, username, upload_key):
        msg = f'Invalid / unknown upload_key {upload_key} for @{username} and {subdomain} organisation.'
        super().__init__(msg)
