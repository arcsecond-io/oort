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

    output = subprocess.run(["supervisord", "-c", conf_file_path], capture_output=True, text=True)
    if "Error: Another program is already listening" in output.stderr:
        p1 = subprocess.Popen(['lsof', '-i', ':9001'], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["grep", "LISTEN"], stdin=p1.stdout, stdout=subprocess.PIPE)
        p3 = subprocess.Popen(["awk", "{print $2}"], stdin=p2.stdout, stdout=subprocess.PIPE, text=True)
        output = p3.communicate()
        port_9001_process_pid = output[0].strip()

        p1 = subprocess.Popen(['lsof', '-a', f'-p{port_9001_process_pid}'], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["grep", "supervisor.sock"], stdin=p1.stdout, stdout=subprocess.PIPE, text=True)
        port_9001_processes = p2.communicate()

        if len(port_9001_processes[0]) > 0:
            print('Supervisor is already running. Fine.')
        else:
            print('Supervisor usual port (9001) is already taken by another process.')
