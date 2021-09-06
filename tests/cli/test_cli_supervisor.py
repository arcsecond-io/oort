import pathlib
from configparser import ConfigParser
from unittest.mock import patch

from oort.cli.supervisor import (
    DEFAULT_PROCESSES,
    get_supervisor_processes_status,
    reconfigure_supervisor,
    start_supervisor_processes,
    stop_supervisor_processes
)
from oort.shared.config import get_oort_supervisor_conf_file_path


def test_reconfigure_supervisor():
    supervisor_conf_file_path = get_oort_supervisor_conf_file_path()
    if supervisor_conf_file_path.exists():
        supervisor_conf_file_path.unlink()  # avoid missing_ok=True parameter which doesn't exist in all Python versions
    reconfigure_supervisor()
    conf = ConfigParser()
    conf.read(str(supervisor_conf_file_path))
    sections = conf.sections()
    assert f'program:{DEFAULT_PROCESSES[0]}' in sections
    assert f'program:{DEFAULT_PROCESSES[1]}' in sections
    assert pathlib.Path(conf.get('program:' + DEFAULT_PROCESSES[0], 'command').split()[-1]).exists()
    assert pathlib.Path(conf.get('program:' + DEFAULT_PROCESSES[1], 'command').split()[-1]).exists()


def test_start_supervisor_processes():
    with patch('subprocess.run') as run:
        start_supervisor_processes()
        run.assert_called_with(
            ['supervisorctl', '-c', str(get_oort_supervisor_conf_file_path()), 'start'] + DEFAULT_PROCESSES)


def test_stop_supervisor_processes():
    with patch('subprocess.run') as run:
        stop_supervisor_processes()
        run.assert_called_with(
            ['supervisorctl', '-c', str(get_oort_supervisor_conf_file_path()), 'stop'] + DEFAULT_PROCESSES,
            capture_output=True)


def test_get_supervisor_processes_status_no_args():
    with patch('subprocess.run') as run:
        get_supervisor_processes_status()
        run.assert_called_with(['supervisorctl', '-c', str(get_oort_supervisor_conf_file_path()), 'status'])


def test_get_supervisor_processes_status_with_args():
    with patch('subprocess.run') as run:
        get_supervisor_processes_status('dummy_arg')
        run.assert_called_with(
            ['supervisorctl', '-c', str(get_oort_supervisor_conf_file_path()), 'status', 'dummy_arg'])
