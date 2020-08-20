from oort.shared.errors import OortCloudError


class UploadPreparationError(OortCloudError):
    pass


class UploadPreparationAPIError(OortCloudError):
    pass


class UploadPreparationFatalError(OortCloudError):
    pass


class UploadRemoteFileCheckError(OortCloudError):
    pass


class UploadPackingError(OortCloudError):
    pass


class PathObservationError(OortCloudError):
    pass


class MultipleDBInstanceError(OortCloudError):
    pass
