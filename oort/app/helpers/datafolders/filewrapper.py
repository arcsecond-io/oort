import json
import os
import uuid

from datetime import datetime

from arcsecond import Arcsecond


class FileWrapper(object):
    def __init__(self, filepath, dataset_uuid, dataset_name, debug=False, organisation=None):
        if not filepath:
            raise ValueError(f'Missing / wrong filepath: {filepath}')
        if not os.path.exists(filepath):
            raise ValueError(f'File not found at path: {filepath}')
        if not os.path.isfile(filepath):
            raise ValueError(f'Filepath is not a file: {filepath}')

        if not dataset_uuid:
            raise ValueError(f'Missing / wrong dataset UUID: {dataset_uuid}')
        try:
            uuid.UUID(dataset_uuid)
        except ValueError:
            raise ValueError(f'Missing / wrong dataset UUID: {dataset_uuid}')

        self.filepath = filepath
        self.dataset_uuid = dataset_uuid
        self.dataset_name = dataset_name
        self.filesize = os.path.getsize(filepath)
        self.status = 'new'
        self.progress = 0
        self.started = None
        self.ended = None
        self.duration = None
        self.result = None
        self.error = None
        self._exists_remotely = False

        self.api = Arcsecond.build_datafiles_api(dataset=dataset_uuid,
                                                 debug=debug,
                                                 organisation=organisation)

        def update_progress(event, progress_percent):
            self.progress = progress_percent
            self.duration = (datetime.now() - self.started).total_seconds()

        self.uploader, _ = self.api.create({'file': filepath}, callback=update_progress)

    @property
    def remaining_bytes(self):
        return (100 - self.progress) * self.filesize / 1000

    def exists_remotely(self):
        if self._exists_remotely:
            return self._exists_remotely

        filename = os.path.basename(self.filepath)
        response_list, error = self.api.list(name=filename)
        if error:
            print(error)

        if isinstance(response_list, dict) and 'count' in response_list.keys() and 'results' in response_list.keys():
            response_list = response_list['results']

        if len(response_list) == 0:
            return False
        elif len(response_list) == 1:
            self._exists_remotely = 'amazonaws.com' in response_list[0].get('file', '')
            return self._exists_remotely
        else:
            print(f'Multiple files for dataset {self.dataset_uuid} and filename {filename}???')
            return False

    def start(self):
        if self.started is not None:
            return
        self.started = datetime.now()
        if self.exists_remotely():
            self.progress = 100
        else:
            self.uploader.start()

    def finish(self):
        if self.ended is not None:
            return

        if not self.exists_remotely():
            _, self.error = self.uploader.finish()

        if self.error:
            self.status = 'error'
            self._process_error(self.error)
        else:
            self.status = 'OK'

        self.progress = 0
        self.ended = datetime.now()
        self.duration = (self.ended - self.started).total_seconds()

    def _process_error(self, error):
        try:
            error_body = json.loads(error)
        except Exception:
            pass
        else:
            if 'detail' in error_body.keys():
                detail = error_body['detail']
                error_content = detail[0] if isinstance(detail, list) and len(detail) > 0 else detail
                if 'already exists in dataset' in error_content:
                    self.error = ''
                    self.status = 'OK'

    def is_started(self):
        return self.started is not None and self.ended is None

    def will_finish(self):
        return self.is_started() and self.progress / 1000 < 100

    def is_finished(self):
        return self.ended is not None and (datetime.now() - self.ended).total_seconds() > 2

    def to_dict(self):
        return {
            'filename': os.path.basename(self.filepath),
            'filepath': self.filepath,
            'filesize': self.filesize,
            'status': self.status,
            'progress': self.progress,
            'started': self.started.strftime('%Y-%m-%dT%H:%M:%S') if self.started else '',
            'ended': self.ended.strftime('%Y-%m-%dT%H:%M:%S') if self.ended else '',
            'duration': '{:.1f}'.format(self.duration) if self.duration else '',
            'dataset_uuid': self.dataset_uuid,
            'dataset_name': self.dataset_name,
            'error': self.error or ''
        }
