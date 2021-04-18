#!/usr/bin/env python3
import signal
import sys
import time

from oort.shared.config import get_config_upload_folder_sections, get_logger
from oort.shared.identity import Identity
from oort.uploader.engine.pathsobserver import PathsObserver
from oort.uploader.engine.zipper import zipper_stop_event

paths_observer = PathsObserver()


def handle_ctrl_c(self, signum, frame):
    self._logger.info(f'Interrupt received: {signum}. Cancelling all zips.')
    zipper_stop_event.set()
    time.sleep(1)
    sys.exit(0)


# Beware only the main thread of the main interpreter is allowed to set a new signal handler.
# https://docs.python.org/3/library/signal.html
signal.signal(signal.SIGINT, handle_ctrl_c)  # Handle Ctrl-C

if __name__ == "__main__":
    debug = len(sys.argv) > 1 and sys.argv[1] in ['-d', '--debug']
    logger = get_logger(debug=debug)
    paths_observer.debug = debug

    logger.info('Starting infinite loop of PathsObserver...')
    paths_observer.start()

    for folder_section in get_config_upload_folder_sections():
        identity = Identity.from_folder_section(folder_section)
        folder_path = folder_section.get('path')
        # paths_observer.observe_folder will deal with the initial walk.
        paths_observer.observe_folder(folder_path, identity)

    try:
        while paths_observer.is_alive():
            paths_observer.join(1)
    except KeyboardInterrupt:
        paths_observer.stop()

    paths_observer.join()
