import importlib
import os
import subprocess

from oort.config import get_supervisor_conf_file_path


def setup_supervisor():
    conf_file_path = get_supervisor_conf_file_path()

    if not os.path.exists(conf_file_path):
        output = subprocess.run(["echo_supervisord_conf"], capture_output=True, text=True)
        conf_content = output.stdout
    else:
        with open(conf_file_path, "r") as f:
            conf_content = f.read()

    spec = importlib.util.find_spec('oort')
    server_command = os.path.join(os.path.dirname(spec.origin), 'server', 'main.py')
    uploader_command = os.path.join(os.path.dirname(spec.origin), 'uploader', 'main.py')

    # Making sure they are executable
    os.chmod(server_command, 0o744)
    os.chmod(uploader_command, 0o744)

    if server_command not in conf_content:
        conf_content += "\n\n"
        conf_content += "[program:oort-server]\n"
        conf_content += f"command={server_command}"

    if uploader_command not in conf_content:
        conf_content += "\n\n"
        conf_content += "[program:oort-uploader]\n"
        conf_content += f"command={uploader_command}"

    with open(conf_file_path, "w") as f:
        f.write(conf_content)
