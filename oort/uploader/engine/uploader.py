import json
import os
import pathlib
import socket
from datetime import datetime

from arcsecond import ArcsecondAPI
from arcsecond.api.endpoints import AsyncFileUploader

from oort import __version__
from oort.shared.config import get_oort_logger
from oort.shared.models import Status, Substatus
from . import errors


class FileUploader(object):
    def __init__(self, pack):
        self._logger = get_oort_logger('uploader', debug=True)

        self._pack = pack
        self._upload = self._pack.upload
        self._final_file_path = pathlib.Path(self._pack.final_file_path)

        is_test_context = bool(os.environ.get('OORT_TESTS') == '1')
        self._api = ArcsecondAPI.datafiles(dataset=str(self._upload.dataset.uuid),  # will be used as request prefix
                                           upload_key=pack.identity.upload_key,
                                           organisation=pack.identity.subdomain,
                                           debug=pack.identity.debug,
                                           test=is_test_context)

    @property
    def log_prefix(self) -> str:
        return f'[FileUploader: {str(self._final_file_path)}]'

    def _prepare_file_uploader(self, remote_resource_exists):
        # Callback allowing for the server monitor to display the percentage of progress of the upload.
        def update_upload_progress(event, progress_percent):
            if progress_percent > self._upload.progress + 0.1 or progress_percent > 99:
                self._upload.smart_update(status=Status.UPLOADING.value,
                                          substatus=Substatus.UPLOADING.value,
                                          progress=progress_percent,
                                          duration=(datetime.now() - self._upload.started).total_seconds())

        ffps = str(self._final_file_path)

        tag_filepath = f'filepath|{ffps}'
        tag_folder = f'folder|{self._pack.clean_folder_name}'
        tag_root = f'root|{self._pack.root_folder_name}'
        tag_origin = f'origin|{socket.gethostname()}|'
        tag_uploader = f'uploader|{ArcsecondAPI.username()}'
        tag_oort = f'oort|{__version__}'

        payload = {'file': ffps, 'tags': [tag_filepath, tag_folder, tag_root, tag_origin, tag_uploader, tag_oort]}

        self._async_file_uploader: AsyncFileUploader
        if remote_resource_exists:
            self._logger.info(f"{self.log_prefix} Remote resource exists. Preparing 'Update' APIs.")
            self._async_file_uploader, error = self._api.update(self._final_file_path.name, payload,
                                                                callback=update_upload_progress)
        else:
            self._logger.info(f"{self.log_prefix} Remote resource does not exist. Preparing 'Create' APIs.")
            self._async_file_uploader, error = self._api.create(payload, callback=update_upload_progress)

        if error is not None:
            msg = f'{self.log_prefix} API preparation error for {ffps}: {str(error)}'
            self._logger.error(msg)

    def _check_remote_resource_and_file(self):
        _remote_resource_exists = False
        _remote_resource_has_file = False

        # self._api contains a reference to the dataset.
        response, error = self._api.read(self._final_file_path.name)

        if error is not None:
            if 'not found' in error.lower():
                # Remote file resource doesn't exists remotely. self._api.create method is fine.
                _remote_resource_exists = False
            else:
                # If for some reason the resource is duplicated, we end up here.
                self._logger.error(f'{self.log_prefix} Check remote file failed with error: {str(error)}')
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

        except (errors.UploadRemoteFileCheckError, Exception) as error:
            self._logger.error(f'{self.log_prefix} {str(error)}')
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
        self._logger.info(f'{self.log_prefix} Starting upload ({self._upload.get_formatted_size()})')

        self._async_file_uploader.start()
        _, upload_error = self._async_file_uploader.finish()

        ended = datetime.now()
        self._upload.smart_update(ended=ended, progress=0, duration=(ended - self._upload.started).total_seconds())

        if upload_error:
            self._logger.info(f'{self.log_prefix} {str(upload_error)}')
            self._process_error(upload_error)
        else:
            msg = f'{self.log_prefix} Successfully uploaded {self._upload.get_formatted_size()}'
            msg += f' in {self._upload.duration} seconds.'
            self._logger.info(msg)
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

    def upload_file(self):
        self._logger.info(f'{self.log_prefix} Opening upload sequence.')
        self._perform()
        self._logger.info(f'{self.log_prefix} Closing upload sequence.')

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
