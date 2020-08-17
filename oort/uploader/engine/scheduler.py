import asyncio

from oort.shared.config import get_logger
from .preparator import UploadPreparator
from .uploader import FileUploader

logger = get_logger()

MAX_TASKS = 3


class UploadScheduler(object):
    def __init__(self):
        self._loop = asyncio.get_event_loop()
        # self._loop.run_forever()
        # Creating a single async Queue
        self._queue = asyncio.Queue(0, loop=self._loop)
        # Creating a limited number of consumers to avoid too many simultaneous call to api.arcsecond.io
        self._consumers = [self._loop.create_task(self._consumer(self._queue)) for _ in range(MAX_TASKS)]

    def __del__(self):
        for _consumer in self._consumers:
            _consumer.cancel()
        self._loop.close()

    async def _consumer(self, queue):
        while True:
            preparator: UploadPreparator = await queue.get()
            await preparator.prepare()
            # file_uploader = FileUploader(preparator.pack, preparator.identity)
            # await file_uploader.upload()
            queue.task_done()

    async def prepare_and_upload(self, preparator: UploadPreparator):
        # Enquing new preparator.
        await self._queue.put(preparator)


scheduler = UploadScheduler()
