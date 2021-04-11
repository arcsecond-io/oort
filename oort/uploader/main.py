#!/usr/bin/env python3
import os
import subprocess
import sys

from oort.shared.config import get_config_upload_folder_sections, get_logger
from oort.shared.identity import Identity
from oort.uploader.engine.pathsobserver import PathsObserver

paths_observer = PathsObserver()

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
