#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_cli
----------------------------------

Tests for `cli` module. CLI interface tests.
"""
import pytest

from contextlib import contextmanager
from click.testing import CliRunner

from pyrelaxmapper import __version__, cli


def test_main():
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'Usage: main [OPTIONS]' in result.output

    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert help_result.output == result.output

    version_result = runner.invoke(cli.main, ['--version'])
    assert version_result.exit_code == 0
    assert "version {}".format(__version__) in version_result.output


def test_make():
    runner = CliRunner()
    result = runner.invoke(cli.make)
    assert result.exit_code == 0
    assert cli.make.__doc__.splitlines()[0] in result.output

    result = runner.invoke(cli.make, ['invalid'])
    assert result.exit_code == 2
    assert '"actions": invalid choice: invalid.' in result.output

    # Best on dummies
    # result = runner.invoke(cli.make, ['clean'])
    # assert result.exit_code == 0
    # assert 'Cleaning all caches, next load will take up to a minute.' in result.output

    # result = runner.invoke(cli.make, ['relax'])
    # assert result.exit_code == 0
    # assert 'Running RL algorithm.' in result.output
    #
    # result = runner.invoke(cli.make, ['stats'])
    # assert result.exit_code == 0
    # assert 'Creating statistics report.' in result.output


def test_config():
    runner = CliRunner()
    result = runner.invoke(cli.config)
    assert result.exit_code == 0
    assert cli.config.__doc__.splitlines()[0] in result.output

    result = runner.invoke(cli.config, ['list'])
    assert result.exit_code == 0
    assert 'Configuration summary:' in result.output

    # With file, check for diffs
    # result = runner.invoke(cli.config, ['list'])
    # assert result.exit_code == 0
    # assert 'Configuration summary:' in result.output

    # result = runner.invoke(cli.config, ['edit'])
    # assert result.exit_code == 0
    # assert 'Usage: main config [OPTIONS]' in result.output


def test_logger():
    runner = CliRunner()
    result = runner.invoke(cli.logger)
    assert result.exit_code == 0
    assert cli.logger.__doc__.splitlines()[0] in result.output

    result = runner.invoke(cli.logger, ['list'])
    assert result.exit_code == 0
    assert 'Logger level' in result.output

    result = runner.invoke(cli.logger, ['select'])
    assert result.exit_code == 0
    assert 'Select logger level.' in result.output

    result = runner.invoke(cli.logger, ['select', '--level=invalid'])
    assert result.exit_code == 2
    assert '"--level": invalid choice: invalid.' in result.output

    levels = {'release': 'RELEASE', 'debug': 'DEBUG'}
    for choice, level in levels.items():
        result = runner.invoke(cli.logger, ['select', '--level={}'.format(choice)])
        assert result.exit_code == 0
        assert 'Logger mode set to {}'.format(level) in result.output

