#!/usr/bin/env python3
import signal
import sys
import time

from oort.shared.config import get_oort_logger
from oort.uploader.engine.pathsobserver import PathsObserver
from oort.uploader.engine.zipper import zipper_stop_event

logger = get_oort_logger('uploader')

paths_observer = PathsObserver()


def handle_ctrl_c(signum, frame):
    logger.info(f'Interrupt received: {signum}. Cancelling all pending operations and exiting.')
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
    paths_observer.debug = debug

    logger.info('Starting thread of PathsObserver...')
    paths_observer.start()

    try:
        while paths_observer.is_alive():
            paths_observer.join(1)
    except KeyboardInterrupt:
        paths_observer.stop()

    paths_observer.join()
