import re
from click.testing import CliRunner
from oort import server


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(server.main, ['-v'])
    assert result.exit_code == 0 and not result.exception
    assert re.match('[0-9].[0-9].[0-9]', result.output)
    result = runner.invoke(server.main, ['--version'])
    assert result.exit_code == 0 and not result.exception
    assert re.match('[0-9].[0-9].[0-9]', result.output)
    result = runner.invoke(server.version)
    assert result.exit_code == 0 and not result.exception
    assert re.match('[0-9].[0-9].[0-9]', result.output)


def test_cli_global_help():
    runner = CliRunner()
    result = runner.invoke(server.main, ['-h'])
    assert result.exit_code == 0 and not result.exception
    assert 'Usage: main [OPTIONS] COMMAND [ARGS]' in result.output
    result = runner.invoke(server.main, ['--help'])
    assert result.exit_code == 0 and not result.exception
    assert 'Usage: main [OPTIONS] COMMAND [ARGS]' in result.output
