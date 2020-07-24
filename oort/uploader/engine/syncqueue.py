import queue

class SyncQueue(object):
    def __init__(self):
        self._queue = queue.Queue()

# sync_queue = queue.Queue()
# # insert items at the end of the queue
# for x in range(4):
#     q.put(str(x))
# # remove items from the head of the queue
# while not q.empty():
#     print(q.get(), end=" ")
# print("\n")
