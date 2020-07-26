import asyncio

from oort.shared.config import get_logger
from .preparator import UploadPreparator
from .uploader import FileUploader

logger = get_logger()

MAX_TASKS = 3


class UploadScheduler(object):
    def __init__(self):
        # Creating a single async Queue
        self._queue = asyncio.Queue()
        # Creating a limited number of consumers to avoid too many simultaneous call to api.arcsecond.io
        self._consumers = [asyncio.create_task(self._consumer(self._queue)) for _ in range(MAX_TASKS)]

    async def _consumer(self, queue):
        while True:
            preparator: UploadPreparator = await queue.get()
            await preparator.prepare()
            file_uploader = FileUploader(preparator.pack, preparator.identity)
            await file_uploader.upload()
            queue.task_done()

    def prepare_and_upload(self, preparator: UploadPreparator):
        # Enquing new preparator.
        self._queue.put(preparator)


scheduler = UploadScheduler()
