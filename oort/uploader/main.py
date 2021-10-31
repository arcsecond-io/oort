#!/usr/bin/env python3
import signal
import sys
import time

from oort.shared.config import get_oort_logger
from oort.uploader.engine.pathsobserver import PathObserverManager
from oort.uploader.engine.zipper import zipper_stop_event

logger = get_oort_logger('uploader')

manager = PathObserverManager()


def handle_ctrl_c(signum, frame):
    logger.info(f'Interrupt received: {signum}. Cancelling all pending operations and exiting.')
    manager.stop_observers()
    zipper_stop_event.set()
    time.sleep(0.1)
    sys.exit(0)


# Beware only the main thread of the main interpreter is allowed to set a new signal handler.
# https://docs.python.org/3/library/signal.html
signal.signal(signal.SIGINT, handle_ctrl_c)  # Handle ctrl-c
signal.signal(signal.SIGQUIT, handle_ctrl_c)  # Handle ctrl-\
signal.signal(signal.SIGTERM, handle_ctrl_c)

if __name__ == "__main__":
    debug = len(sys.argv) > 1 and sys.argv[1] in ['-d', '--debug']
    manager.debug = debug

    logger.info('Starting thread of PathObserverManager...')
    manager.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop_observers()

    manager.join()
