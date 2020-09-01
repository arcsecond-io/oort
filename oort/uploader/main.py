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
        username = folder_section.get('username', '')
        api_key = folder_section.get('api_key', '')
        subdomain = folder_section.get('subdomain', '')
        role = folder_section.get('role', '')
        telescope = folder_section.get('telescope', '')
        longitude = folder_section.get('longitude', '')

        script_path = os.path.join(os.path.dirname(__file__), 'engine', 'initial_walk.py')
        identity = Identity(username, api_key, subdomain, role, telescope, longitude, debug)

        # Using run instead of Popen(close_fds=True) will run the initial_walk in a synchronous way.
        subprocess.run(["python3", script_path, folder_section.get('path'), identity.get_args_string()])
        paths_observer.observe_folder(folder_section['path'], identity)

    try:
        while paths_observer.is_alive():
            paths_observer.join(1)
    except KeyboardInterrupt:
        paths_observer.stop()

    paths_observer.join()
