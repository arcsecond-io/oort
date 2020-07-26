from oort.shared.config import get_logger
from .preparator import UploadPreparator
from .uploader import FileUploader

logger = get_logger()

MAX_TASKS = 3


class UploadScheduler(object):
    def __init__(self):
        self._queue = []
        self._count = 0

    def prepare_and_upload(self, preparator: UploadPreparator):
        if self._count < MAX_TASKS:
            self._count += 1
            await preparator.prepare()
            file_uploader = FileUploader(preparator.pack, preparator.identity)
            await file_uploader.upload()
            self._count -= 1
            if len(self._queue) > 0:
                self.prepare_and_upload(self._queue.pop())
        else:
            self._queue.append(preparator)


scheduler = UploadScheduler()
