import json
import os
import socket
from datetime import datetime
from pathlib import Path

from arcsecond import ArcsecondAPI
from arcsecond.api.endpoints import AsyncFileUploader

from oort import __version__
from oort.common.constants import Status, Substatus
from oort.common.identity import Identity
from oort.common.logger import get_oort_logger
from .errors import UploadRemoteDatasetCheckError, UploadRemoteFileCheckError


class FileUploader(object):
    def __init__(self, identity: Identity, root_path: Path, file_path: Path, display_progress: bool = False):
        self._identity = identity
        self._root_path = root_path
        self._file_path = file_path
        self._display_progress = display_progress

        self._logger = get_oort_logger(debug=True)
        self._started = None
        self._progress = 0
        self._is_test_context = bool(os.environ.get('OORT_TESTS') == '1')

        self._dataset = None
        self._api = None

    @property
    def log_prefix(self) -> str:
        return f'[FileUploader: {str(self._file_path)}]'

    def _prepare_dataset(self):
        _api = ArcsecondAPI.datasets(upload_key=self._identity.upload_key,
                                     organisation=self._identity.subdomain,
                                     api=self._identity.api,
                                     test=self._is_test_context)

        if self._identity.dataset_uuid:
            response, error = _api.read(self._identity.dataset_uuid)
            if error:
                raise UploadRemoteDatasetCheckError(str(error))
            self._dataset = response

        elif self._identity.dataset_name:
            # Dataset UUID is empty, and CLI validators have already checked this dataset doesn't exist.
            # Simply create dataset.
            response, error = _api.create(**{'name': self._identity.dataset_name})
            if error:
                raise UploadRemoteDatasetCheckError(str(error))
            self._dataset = response

        else:
            raise UploadRemoteDatasetCheckError('No dataset specified.')

        self._api = ArcsecondAPI.datafiles(dataset=str(self._dataset.get('uuid')),  # will be used as request prefix
                                           upload_key=self._identity.upload_key,
                                           organisation=self._identity.subdomain,
                                           api=self._identity.api,
                                           test=self._is_test_context)

    def _prepare_file_uploader(self, remote_resource_exists):
        self._has_logged_final = False
        self._started = datetime.now()

        # Callback allowing for the server monitor to display the percentage of progress of the upload.
        def update_upload_progress(event, progress_percent):
            if progress_percent > self._progress + 0.1 or 99 < progress_percent <= 100:
                duration = (datetime.now() - self._started).total_seconds()
                if self._display_progress is True:
                    print(f"{progress_percent:.2f}% ({duration:.2f} sec)", end="\r")

            self._progress = progress_percent

            if progress_percent >= 100 and self._display_progress and not self._has_logged_final:
                self._logger.info(f"{self.log_prefix} Upload to Arcsecond finished.")
                self._logger.info(f"{self.log_prefix} Now parsing headers & saving file in Storage.")
                self._logger.info(f"{self.log_prefix} It may takes a few seconds.")
                self._has_logged_final = True

        self._async_file_uploader: AsyncFileUploader
        if remote_resource_exists:
            self._logger.info(f"{self.log_prefix} Remote resource exists. Preparing 'Update' APIs.")
            self._async_file_uploader, error = self._api.update(self._file_path.name,
                                                                {'file': str(self._file_path)},
                                                                callback=update_upload_progress)
        else:
            self._logger.info(f"{self.log_prefix} Remote resource does not exist. Preparing 'Create' APIs.")
            self._async_file_uploader, error = self._api.create({'file': str(self._file_path)},
                                                                callback=update_upload_progress)

        if error is not None:
            msg = f'{self.log_prefix} API preparation error for {str(self._file_path)}: {str(error)}'
            self._logger.error(msg)

    def _check_remote_resource_and_file(self):
        _remote_resource_exists = False
        _remote_resource_has_file = False

        # self._api contains a reference to the dataset.
        response, error = self._api.read(self._file_path.name)

        if error is not None:
            if 'not found' in error.lower():
                # Remote file resource doesn't exist remotely. self._api.create method is fine.
                _remote_resource_exists = False
            else:
                # If for some reason the resource is duplicated, we end up here.
                self._logger.error(f'{self.log_prefix} Check remote file failed with error: {str(error)}')
                raise UploadRemoteFileCheckError(str(error))
        else:
            _remote_resource_exists = True
            _remote_resource_has_file = 's3.amazonaws.com' in response.get('file', '')

        if _remote_resource_has_file is False:
            self._prepare_file_uploader(_remote_resource_exists)

        return _remote_resource_has_file

    def _should_perform_upload(self):
        _should_perform = False

        try:
            exists_remotely = self._check_remote_resource_and_file()

        except (UploadRemoteFileCheckError, Exception) as error:
            self._logger.error(f'{self.log_prefix} {str(error)}')

        else:
            if exists_remotely:
                self._logger.info(f'{self.log_prefix} File already uploaded.')
            else:
                _should_perform = True

        return _should_perform

    def _process_upload_error(self, error):
        try:
            error_body = json.loads(error)
        except Exception as err:
            self._logger.error(str(err))
        else:
            if 'detail' in error_body.keys():
                detail = error_body['detail']
                error_content = detail[0] if isinstance(detail, list) and len(detail) > 0 else detail

    def _perform_upload(self):
        file_size = self._file_path.stat().st_size
        self._logger.info(f'{self.log_prefix} Starting upload to Arcsecond ({file_size})')

        self._async_file_uploader.start()
        _, upload_error = self._async_file_uploader.finish()

        ended = datetime.now()
        duration = (ended - self._started).total_seconds()

        if upload_error:
            self._logger.info(f'{self.log_prefix} {str(upload_error)}')
            self._process_upload_error(upload_error)
        else:
            self._logger.info(f'{self.log_prefix} Successfully uploaded {file_size} in {duration} seconds.')

    def _update_file_tags(self):
        # Definition of meaningful tags
        tag_root = f'oort|root|{str(self._root_path)}'
        tag_origin = f'oort|origin|{socket.gethostname()}'
        tag_uploader = f'oort|uploader|{ArcsecondAPI.username(api=self._identity.api)}'
        tag_oort = f'oort|version|{__version__}'

        tags = [tag_root, tag_origin, tag_uploader, tag_oort]
        _, error = self._api.update(self._file_path.name, {'tags': tags})

        if error is not None:
            self._logger.error(f'{self.log_prefix} {str(error)}')

    def upload_file(self):
        self._logger.info(f'{self.log_prefix} Preparing Dataset...')
        self._prepare_dataset()

        self._logger.info(f'{self.log_prefix} Opening upload sequence.')
        if self._should_perform_upload():
            self._perform_upload()
        self._logger.info(f'{self.log_prefix} Closing upload sequence.')

        self._logger.info(f'{self.log_prefix} Updating file tags.')
        self._update_file_tags()

# def test_upload():
#     root = '/Users/onekiloparsec/code/onekiloparsec/arcsecond-oort/data/test_folder/'
#     identity = Identity('cedric', '764837d11cf32dda5f71df24d4a017a4', None, None, None, True)
#     pack = UploadPack(root, os.path.join(root, 'jup999.fits'), identity)
#     uploader = FileUploader(pack._upload, identity)
#     uploader.upload()
