from common.errors import OortCloudError


class UploadRemoteFileCheckError(OortCloudError):
    pass


class UploadPreparationError(OortCloudError):
    pass


class UploadPreparationAPIError(OortCloudError):
    pass


class UploadPreparationFatalError(OortCloudError):
    pass


class UploadPackingError(OortCloudError):
    pass
