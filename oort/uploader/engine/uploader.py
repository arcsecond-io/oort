import json
import os
from datetime import datetime

from arcsecond import ArcsecondAPI
from arcsecond.api.endpoints import AsyncFileUploader

from oort.shared.config import get_logger
from oort.shared.identity import Identity
from oort.shared.models import (
    Dataset,
    STATUS_CHECKING,
    STATUS_ERROR,
    STATUS_OK,
    SUBSTATUS_ALREADY_SYNCED,
    SUBSTATUS_CHECKING,
    SUBSTATUS_DONE,
    SUBSTATUS_ERROR,
    SUBSTATUS_FINISHING,
    SUBSTATUS_REMOTE_CHECK_ERROR,
    SUBSTATUS_STARTING,
    SUBSTATUS_UPLOADING,
    SUBSTATUS_WILL_RESTART,
    Upload
)
from .errors import UploadRemoteFileCheckError
from .packer import UploadPack


class FileUploader(object):
    def __init__(self, pack: UploadPack, identity: Identity, dataset: Dataset):
        self._pack = pack
        self._identity = identity
        self._dataset = dataset
        self._logger = get_logger(debug=True)

        self._upload, _ = Upload.get_or_create(file_path=self._pack.file_path)
        self._upload.smart_update(file_date=self._pack.file_date,
                                  file_size=self._pack.file_size,
                                  dataset=dataset)

        self._stalled_progress = 0
        self._exists_remotely = False
        self._api = None

    @property
    def prefix(self) -> str:
        return '[' + '/'.join(self._pack.file_path.split(os.sep)[-2:]) + ']'

    def _prepare(self):
        if self._identity.organisation is None or len(self._identity.organisation) == 0:
            self._api = ArcsecondAPI.datafiles(dataset=str(self._dataset.uuid),
                                               debug=self._identity.debug,
                                               api_key=self._identity.api_key)
        else:
            self._api = ArcsecondAPI.datafiles(dataset=str(self._dataset.uuid),
                                               debug=self._identity.debug,
                                               organisation=self._identity.organisation)

        def update_progress(event, progress_percent):
            if progress_percent > self._upload.progress + 0.1 or progress_percent > 99:
                self._upload.smart_update(status=STATUS_OK,
                                          substatus=SUBSTATUS_UPLOADING,
                                          progress=progress_percent,
                                          duration=(datetime.now() - self._upload.started).total_seconds())

        self._async_file_uploader: AsyncFileUploader
        self._async_file_uploader, _ = self._api.create({'file': self._pack.file_path}, callback=update_progress)

    def _check_remote_file(self):
        if self._exists_remotely is True:
            return self._exists_remotely

        response, error = self._api.read(os.path.basename(self._pack.file_path))

        if error:
            if 'not found' in error.lower():
                self._exists_remotely = False
            else:
                self._logger.info(f'{self.prefix} {str(error)}')
                raise UploadRemoteFileCheckError(str(error))
        else:
            self._exists_remotely = 'amazonaws.com' in response.get('file', '')

        return self._exists_remotely

    def _start(self):
        if self._upload.started is not None:
            self._logger.info(f'{self.prefix} {self._upload.status} {self._upload.substatus}')
            return

        self._upload.smart_update(started=datetime.now())

        try:
            self._upload.smart_update(status=STATUS_CHECKING, substatus=SUBSTATUS_CHECKING)
            exists_remotely = self._check_remote_file()
        except UploadRemoteFileCheckError as error:
            self._finish()
            self._upload.smart_update(status=STATUS_ERROR, substatus=SUBSTATUS_REMOTE_CHECK_ERROR, error=str(error))
            self._logger.info(f'{self.prefix} {str(error)}')
        except Exception as error:
            self._finish()
            self._upload.smart_update(status=STATUS_ERROR, substatus=SUBSTATUS_ERROR, error=str(error))
            self._logger.info(f'{self.prefix} {str(error)}')
        else:
            if exists_remotely:
                self._finish()
                self._upload.smart_update(status=STATUS_OK, substatus=SUBSTATUS_ALREADY_SYNCED, error='')
                self._logger.info(f'{self.prefix} Already synced.')
            else:
                self._upload.smart_update(status=STATUS_OK, substatus=SUBSTATUS_STARTING, error='')
                self._logger.info(f'{self.prefix} Starting upload.')
                self._async_file_uploader.start()

    def _finish(self):
        if self._upload.ended is not None:
            return

        self._upload.smart_update(status=STATUS_OK, substatus=SUBSTATUS_FINISHING)
        _, upload_error = self._async_file_uploader.finish()

        ended = datetime.now()
        self._upload.smart_update(ended=ended, progress=0, duration=(ended - self._upload.started).total_seconds())

        if upload_error:
            self._logger.info(f'{self.prefix} {str(upload_error)}')
            self._process_error(upload_error)
        else:
            self._logger.info(f'{self.prefix} successfully uploaded in {self._upload.duration} seconds.')
            self._upload.smart_update(status=STATUS_OK, substatus=SUBSTATUS_DONE, error='')

    def _process_error(self, error):
        status, substatus, error = STATUS_ERROR, SUBSTATUS_ERROR, str(error)

        try:
            error_body = json.loads(error)
        except Exception as err:
            if self._identity.debug:
                print(str(err))
            pass
        else:
            if 'detail' in error_body.keys():
                detail = error_body['detail']
                error_content = detail[0] if isinstance(detail, list) and len(detail) > 0 else detail
                if 'already exists in dataset' in error_content:
                    status, substatus, error = STATUS_OK, SUBSTATUS_ALREADY_SYNCED, ''

        self._upload.smart_update(status=status, substatus=substatus, error=error)

    async def upload(self):
        self._logger.info(f'{self.prefix} Preparing upload.')
        self._prepare()
        self._start()
        self._finish()
        self._logger.info(f'{self.prefix} Closing.')

    @property
    def is_started(self):
        return self._upload.started is not None and self._upload.ended is None

    @property
    def is_finished(self):
        return self._upload.started is not None and self._upload.ended is not None

    @property
    def should_restart(self):
        return self._upload.substatus == SUBSTATUS_WILL_RESTART

    @property
    def state(self):
        if not self.is_started() and not self.is_finished():
            return 'pending'
        elif self.is_started() and not self.is_finished():
            return 'current'
        elif self.is_finished():
            return 'finished'


async def test_upload():
    root = '/Users/onekiloparsec/code/onekiloparsec/arcsecond-oort/data/test_folder/'
    dataset = Dataset.get(Dataset.uuid == '4968f81d-77cc-4f16-b83a-5a0587235a56')
    identity = Identity('cedric', '764837d11cf32dda5f71df24d4a017a4', None, None, None, True)
    pack = UploadPack(root, os.path.join(root, 'jup999.fits'))
    uploader = FileUploader(pack=pack, identity=identity, dataset=dataset)
    await uploader.upload()
