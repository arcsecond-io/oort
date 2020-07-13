import os
import subprocess

from oort.config import get_supervisor_conf_file_path


def setup_supervisor():
    if not os.path.exists(get_supervisor_conf_file_path()):
        output = subprocess.run(["echo_supervisord_conf"], capture_output=True, text=True)
        with open(get_supervisor_conf_file_path(), "w") as f:
            f.write(output.stdout)
