import json
import os
from datetime import datetime

from arcsecond import ArcsecondAPI
from arcsecond.api.endpoints import AsyncFileUploader

from oort.shared.config import get_logger
from oort.shared.models import Status, Substatus
from . import errors


class FileUploader(object):
    def __init__(self, pack):
        self._logger = get_logger(debug=True)
        self._pack = pack
        self._upload = self._pack.upload
        self._final_file_path = self._pack.final_file_path
        self._dataset_uuid = self._upload.dataset.uuid

        self._stalled_progress = 0
        test = os.environ.get('OORT_TESTS') == '1'

        # If we have an api_key, hence it is an oort_key, hence we upload for a custom astronomer.
        if self._pack.identity.api_key:
            self._api = ArcsecondAPI.datafiles(dataset=str(self._dataset_uuid),
                                               debug=pack.identity.debug,
                                               test=test,
                                               api_key=pack.identity.api_key)
        else:
            self._api = ArcsecondAPI.datafiles(dataset=str(self._dataset_uuid),
                                               debug=pack.identity.debug,
                                               test=test,
                                               organisation=pack.identity.subdomain)

    @property
    def log_prefix(self) -> str:
        return '[FileUploader: ' + '/'.join(self._final_file_path.split(os.sep)[-2:]) + ']'

    def _prepare_file_uploader(self, remote_resource_exists):
        def update_upload_progress(event, progress_percent):
            if progress_percent > self._upload.progress + 0.1 or progress_percent > 99:
                self._upload.smart_update(status=Status.UPLOADING.value,
                                          substatus=Substatus.UPLOADING.value,
                                          progress=progress_percent,
                                          duration=(datetime.now() - self._upload.started).total_seconds())

        self._async_file_uploader: AsyncFileUploader
        if remote_resource_exists:
            self._logger.info(f"{self.log_prefix} Remote resource exists. Preparing 'Update' APIs.")
            self._async_file_uploader, _ = self._api.update(os.path.basename(self._final_file_path),
                                                            {'file': self._final_file_path},
                                                            callback=update_upload_progress)
        else:
            self._logger.info(f"{self.log_prefix} Remote resource does not exist. Preparing 'Create' APIs.")
            self._async_file_uploader, error = self._api.create({'file': self._final_file_path},
                                                                callback=update_upload_progress)

    def _check_remote_resource_and_file(self):
        _remote_resource_exists = False
        _remote_resource_has_file = False

        response, error = self._api.read(os.path.basename(self._final_file_path))

        if error:
            if 'not found' in error.lower():
                # Remote file resource doesn't exists remotely. self._api.create method is fine.
                _remote_resource_exists = False
            else:
                # If for some reason the resource is duplicated, we end up here.
                self._logger.info(f'{self.log_prefix} Check remote file failed with error: {str(error)}')
                raise errors.UploadRemoteFileCheckError(str(error))
        else:
            _remote_resource_exists = True
            _remote_resource_has_file = 's3.amazonaws.com' in response.get('file', '')

        if _remote_resource_has_file is False:
            self._prepare_file_uploader(_remote_resource_exists)

        return _remote_resource_has_file

    def _check(self):
        _should_perform = False
        self._upload.smart_update(started=datetime.now())

        try:
            self._upload.smart_update(status=Status.UPLOADING.value, substatus=Substatus.CHECKING.value)
            exists_remotely = self._check_remote_resource_and_file()

        except errors.UploadRemoteFileCheckError as error:
            self._logger.info(f'{self.log_prefix} {str(error)}')
            self._upload.smart_update(status=Status.ERROR.value,
                                      substatus=Substatus.ERROR.value,
                                      error=str(error),
                                      ended=datetime.now(),
                                      progress=0,
                                      duration=0)

        except Exception as error:
            self._logger.info(f'{self.log_prefix} {str(error)}')
            self._upload.smart_update(status=Status.ERROR.value,
                                      substatus=Substatus.ERROR.value,
                                      error=str(error),
                                      ended=datetime.now(),
                                      progress=0,
                                      duration=0)

        else:
            if exists_remotely:
                self._logger.info(f'{self.log_prefix} Already synced.')
                self._upload.smart_update(status=Status.OK.value,
                                          substatus=Substatus.ALREADY_SYNCED.value,
                                          error='',
                                          ended=datetime.now(),
                                          progress=0,
                                          duration=0)
            else:
                _should_perform = True

        return _should_perform

    def _perform(self):
        if not self._check():
            return

        self._upload.smart_update(status=Status.UPLOADING.value, substatus=Substatus.STARTING.value, error='')
        self._logger.info(f'{self.log_prefix} Starting upload.')

        self._async_file_uploader.start()
        _, upload_error = self._async_file_uploader.finish()

        ended = datetime.now()
        self._upload.smart_update(ended=ended, progress=0, duration=(ended - self._upload.started).total_seconds())

        if upload_error:
            self._logger.info(f'{self.log_prefix} {str(upload_error)}')
            self._process_error(upload_error)
        else:
            self._logger.info(f'{self.log_prefix} successfully uploaded in {self._upload.duration} seconds.')
            self._upload.smart_update(status=Status.OK.value, substatus=Substatus.DONE.value, error='')

    def _process_error(self, error):
        status, substatus, error = Status.ERROR.value, Substatus.ERROR.value, str(error)

        try:
            error_body = json.loads(error)
        except Exception as err:
            self._logger.error(str(err))
        else:
            if 'detail' in error_body.keys():
                detail = error_body['detail']
                error_content = detail[0] if isinstance(detail, list) and len(detail) > 0 else detail
                if 'already exists in dataset' in error_content:
                    status, substatus, error = Status.OK.value, Substatus.ALREADY_SYNCED.value, ''

        self._upload.smart_update(status=status, substatus=substatus, error=error)

    def upload(self):
        self._logger.info(f'{self.log_prefix} Starting file upload....')
        self._perform()
        self._logger.info(f'{self.log_prefix} Closing file upload.')

    @property
    def is_started(self):
        return self._upload.started is not None and self._upload.ended is None

    @property
    def is_finished(self):
        return self._upload.started is not None and self._upload.ended is not None

    @property
    def state(self):
        if not self.is_started() and not self.is_finished():
            return 'pending'
        elif self.is_started() and not self.is_finished():
            return 'current'
        elif self.is_finished():
            return 'finished'

# def test_upload():
#     root = '/Users/onekiloparsec/code/onekiloparsec/arcsecond-oort/data/test_folder/'
#     identity = Identity('cedric', '764837d11cf32dda5f71df24d4a017a4', None, None, None, True)
#     pack = UploadPack(root, os.path.join(root, 'jup999.fits'), identity)
#     uploader = FileUploader(pack._upload, identity)
#     uploader.upload()
