#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_pyrelaxmapper
----------------------------------

Tests for `pyrelaxmapper` module.
"""
import pytest

from contextlib import contextmanager
from click.testing import CliRunner

from pyrelaxmapper import __version__, cli


def test_command_line_interface():
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
