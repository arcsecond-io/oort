import json
import os
from datetime import datetime

from arcsecond import ArcsecondAPI

from oort.shared.config import get_logger
from oort.shared.identity import Identity
from oort.shared.models import Dataset, Upload
from .packer import UploadPack


class FileUploader(object):
    def __init__(self, pack: UploadPack, identity: Identity, dataset: Dataset):
        self._pack = pack
        self._identity = identity
        self._dataset = dataset

        self._logger = get_logger(debug=True)

        self.filesize = os.path.getsize(self._pack.file_path)
        self.status = 'ready'
        self.substatus = 'pending'
        self.progress = 0
        self.started = None
        self.ended = None
        self.duration = None
        self.result = None
        self.error = None

        self._stalled_progress = 0
        self._exists_remotely = False
        self.api = None

    @property
    def log_string(self):
        log_string = f' {self._pack.file_path} {self._pack.night_log_date_string}'
        # log_string += f'ds_{self.dataset["uuid"]} nl_{self.night_log["uuid"]} tel_{self.telescope["uuid"]} '
        # log_string += f'as_{self.astronomer[0] if self.astronomer else ""} org_{self.organisation}'
        return log_string

    def _prepare(self):
        if self._identity.organisation is None or len(self._identity.organisation) == 0:
            self.api = ArcsecondAPI.datafiles(dataset=str(self._dataset.uuid),
                                              debug=self._identity.debug,
                                              api_key=self._identity.api_key)
        else:
            self.api = ArcsecondAPI.datafiles(dataset=str(self._dataset.uuid),
                                              debug=self._identity.debug,
                                              organisation=self._identity.organisation)

        def update_progress(event, progress_percent):
            self.status = 'OK'
            self.substatus = 'uploading...'
            self.progress = progress_percent
            self.duration = (datetime.now() - self.started).total_seconds()

        self.uploader, _ = self.api.create({'file': self._pack.file_path}, callback=update_progress)

    def _check_remote_file(self):
        if self._exists_remotely is True:
            return self._exists_remotely

        filename = os.path.basename(self._pack.file_path)
        response_list, error = self.api.list(name=filename)
        if error:
            raise Exception(str(error)[:20] + '...')

        # Dealing with pagination
        if isinstance(response_list, dict) and 'results' in response_list.keys():
            response_list = response_list['results']

        if len(response_list) > 1:
            raise Exception(f'multiple files?')

        if len(response_list) == 1:
            self._exists_remotely = 'amazonaws.com' in response_list[0].get('file', '')

        return self._exists_remotely

    def _start(self):
        if self.started is not None:
            return

        self.started = datetime.now()

        try:
            self.status, self.substatus = 'checking', 'asking arcsecond.io...'
            exists_remotely = self._check_remote_file()
        except Exception as error:
            self._logger.info('error' + self.log_string + f' {str(self.error)}')
            self._finish()
            self.status = '?'
            self.substatus = str(error)
        else:
            if exists_remotely:
                self._finish()
                self.status, self.substatus = 'OK', 'already synced'
            else:
                self._logger.info(str.ljust('start', 5) + self.log_string)
                self.status, self.substatus = 'OK', 'starting'
                self.uploader.start()

    def _finish(self):
        if self.ended is not None:
            return

        self.substatus = 'finishing...'
        _, self.error = self.uploader.finish()

        self.ended = datetime.now()
        self.progress = 0
        self.duration = (self.ended - self.started).total_seconds()

        if self.error:
            self._logger.info('error' + self.log_string + f' {str(self.error)}')
            self.status = 'error'
            self.substatus = str(self.error)[:20] + '...'
            self._process_error(self.error)
        else:
            self._logger.info(str.ljust('ok', 5) + self.log_string)
            self.status = 'OK'
            self.substatus = 'Done'

    def _process_error(self, error):
        try:
            error_body = json.loads(error)
        except Exception as err:
            if self._identity.debug: print(str(err))
            pass
        else:
            if 'detail' in error_body.keys():
                detail = error_body['detail']
                error_content = detail[0] if isinstance(detail, list) and len(detail) > 0 else detail
                if 'already exists in dataset' in error_content:
                    self.error = ''
                    self.status = 'OK'
                    self.substatus = 'already synced'

    async def upload(self):
        self._logger.info('Preparing upload.')
        self._prepare()
        self._logger.info('Starting upload.')
        self._start()
        self._logger.info('Finished upload.')
        self._finish()
        self._logger.info('Upload done.')

    @property
    def is_started(self):
        return self.started is not None and self.ended is None

    @property
    def is_finished(self):
        return self.started is not None and self.ended is not None

    @property
    def state(self):
        if not self.is_started() and not self.is_finished():
            return 'pending'
        elif self.is_started() and not self.is_finished():
            return 'current'
        elif self.is_finished():
            return 'finished'

    # def to_dict(self):
    #     self._check_stalled()
    #     return {
    #         'filename': os.path.basename(self.filepath),
    #         'filepath': self.filepath,
    #         'filesize': self.filesize,
    #         'filedate': self.filedate.isoformat(),
    #         'status': self.status,
    #         'substatus': self.substatus,
    #         'progress': self.progress,
    #         'started': self.started.strftime('%Y-%m-%dT%H:%M:%S') if self.started else '',
    #         'ended': self.ended.strftime('%Y-%m-%dT%H:%M:%S') if self.ended else '',
    #         'duration': '{:.1f}'.format(self.duration) if self.duration else '',
    #         'dataset': self.dataset,
    #         'night_log': self.night_log,
    #         'telescope': self.telescope,
    #         'organisation': self.organisation or '',
    #         'astronomer': self.astronomer[0] if self.astronomer else '',
    #         'error': self.error or '',
    #         'state': self.state
    #     }
