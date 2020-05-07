import json
import os
import uuid

from datetime import datetime
from arcsecond import Arcsecond

from .utils import get_oort_logger

logger = get_oort_logger()


class FileUploader(object):
    def __init__(self,
                 filepath: str,
                 filedate: datetime,
                 astronomer: tuple,
                 organisation: str,
                 debug: bool,
                 verbose: bool):

        if not filepath:
            raise ValueError(f'Missing / wrong filepath: {filepath}')
        if not os.path.exists(filepath):
            raise ValueError(f'File not found at path: {filepath}')
        if not os.path.isfile(filepath):
            raise ValueError(f'Filepath is not a file: {filepath}')
        if not filedate:
            raise ValueError(f'Missing / wrong filedate: {filedate}')

        self.filepath = filepath
        self.filedate = filedate
        self.astronomer = astronomer
        self.organisation = organisation

        self.debug = debug
        self.verbose = verbose

        self.dataset = None
        self.night_log = None
        self.telescope = None

        self.filesize = os.path.getsize(filepath)
        self.status = 'ready'
        self.substatus = 'pending'
        self.progress = 0
        self.started = None
        self.ended = None
        self.duration = None
        self.result = None
        self.error = None

        self._exists_remotely = False
        self.api = None

    @property
    def log_string(self):
        log_string = f' {self.filepath} {self.filedate}'
        log_string += f'ds_{self.dataset["uuid"]} nl_{self.night_log["uuid"]} tel_{self.telescope["uuid"]} '
        log_string += f'as_{self.astronomer[0] if self.astronomer else ""} org_{self.organisation}'
        return log_string

    def prepare(self, dataset, night_log, telescope):
        if not dataset or not dataset['uuid']:
            raise ValueError(f'Missing / wrong dataset UUID: {dataset["uuid"]}')
        try:
            uuid.UUID(dataset['uuid'])
        except ValueError:
            raise ValueError(f'Missing / wrong dataset UUID: {dataset["uuid"]}')

        self.dataset = dataset
        self.night_log = night_log
        self.telescope = telescope

        if self.astronomer:
            self.api = Arcsecond.build_datafiles_api(dataset=self.dataset['uuid'],
                                                     debug=self.debug,
                                                     api_key=self.astronomer[1])
        else:
            self.api = Arcsecond.build_datafiles_api(dataset=self.dataset['uuid'],
                                                     debug=self.debug,
                                                     organisation=self.organisation)

        def update_progress(event, progress_percent):
            self.status = 'OK'
            self.substatus = 'uploading...'
            self.progress = progress_percent
            self.duration = (datetime.now() - self.started).total_seconds()

        self.uploader, _ = self.api.create({'file': self.filepath}, callback=update_progress)

    def _check_remote_file(self):
        if self._exists_remotely is True:
            return self._exists_remotely

        filename = os.path.basename(self.filepath)
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

    def start(self):
        if self.dataset is None:
            raise Exception("Missing dataset. Can't start upload.")

        if self.started is not None:
            return

        self.started = datetime.now()

        try:
            self.status, self.substatus = 'checking', 'asking arcsecond.io...'
            exists_remotely = self._check_remote_file()
        except Exception as error:
            logger.info('error' + self.log_string + f' {str(self.error)}')
            self.finish()
            self.status = '?'
            self.substatus = str(error)
        else:
            if exists_remotely:
                self.finish()
                self.status, self.substatus = 'OK', 'already synced'
            else:
                logger.info(str.ljust('start', 5) + self.log_string)
                self.status, self.substatus = 'OK', 'starting'
                self.uploader.start()

    def finish(self):
        if self.ended is not None:
            return

        _, self.error = self.uploader.finish()

        self.ended = datetime.now()
        self.progress = 0
        self.duration = (self.ended - self.started).total_seconds()

        if self.error:
            logger.info('error' + self.log_string + f' {str(self.error)}')
            self.status = 'error'
            self.substatus = str(self.error)[:20] + '...'
            self._process_error(self.error)
        else:
            logger.info(str.ljust('ok', 5) + self.log_string)
            self.status = 'OK'
            self.substatus = 'Done'

    def _process_error(self, error):
        try:
            error_body = json.loads(error)
        except Exception as err:
            if self.debug or self.verbose: print(str(err))
            pass
        else:
            if 'detail' in error_body.keys():
                detail = error_body['detail']
                error_content = detail[0] if isinstance(detail, list) and len(detail) > 0 else detail
                if 'already exists in dataset' in error_content:
                    self.error = ''
                    self.status = 'OK'
                    self.substatus = 'already synced'

    def is_started(self):
        return self.started is not None and self.ended is None

    def is_finished(self):
        return self.started is not None and self.ended is not None

    def can_finish(self):
        return self.is_started() and self.progress >= 99

    def to_dict(self):
        return {
            'filename': os.path.basename(self.filepath),
            'filepath': self.filepath,
            'filesize': self.filesize,
            'filedate': self.filedate.isoformat(),
            'status': self.status,
            'substatus': self.substatus,
            'progress': self.progress,
            'started': self.started.strftime('%Y-%m-%dT%H:%M:%S') if self.started else '',
            'ended': self.ended.strftime('%Y-%m-%dT%H:%M:%S') if self.ended else '',
            'duration': '{:.1f}'.format(self.duration) if self.duration else '',
            'dataset': self.dataset,
            'night_log': self.night_log,
            'telescope': self.telescope,
            'organisation': self.organisation or '',
            'astronomer': self.astronomer[0] if self.astronomer else '',
            'error': self.error or ''
        }
