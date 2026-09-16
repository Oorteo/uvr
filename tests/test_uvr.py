# SPDX-FileCopyrightText: 2026 Authors (see git history)
# SPDX-License-Identifier: MIT

import os
import sys

import pytest

from uvr import (
    _find_venv_python,
    _is_offline,
    _venv_python_at,
    resolve_argv,
)


def test_resolve_argv():
    this_script = os.path.realpath(__file__)
    this_script_dir = os.path.dirname(this_script)

    # Test case 1: No arguments
    sys.argv = ['uvr']
    pre_opt, run_script, post_opt = resolve_argv()
    assert pre_opt == []
    assert run_script is None
    assert post_opt == []

    # Test case 2: Only pre-options
    sys.argv = ['uvr', '-v', '--']
    pre_opt, run_script, post_opt = resolve_argv()
    assert pre_opt == ['-v']
    assert run_script is None
    assert post_opt == []

    # Test case 3: Pre-options and script
    sys.argv = ['uvr', '-v', 'foo.py', 'arg1', 'arg2']
    pre_opt, run_script, post_opt = resolve_argv()
    assert pre_opt == [
        '-v',
    ]
    assert run_script == 'foo.py'
    assert post_opt == ['arg1', 'arg2']

    # Test case 4: Only script
    sys.argv = ['uvr', 'foo.py']
    pre_opt, run_script, post_opt = resolve_argv()
    assert pre_opt == []
    assert run_script == 'foo.py'
    assert post_opt == []

    # Test case 5: Script with pre-options and post-options
    sys.argv = ['uvr', '-v', '--script', 'foo.py', '--option1', '--option2']
    pre_opt, run_script, post_opt = resolve_argv()
    assert pre_opt == ['-v', '--script']
    assert run_script == 'foo.py'
    assert post_opt == ['--option1', '--option2']

    # Test case 6: Script with pre-options and post-options
    sys.argv = ['uvr', '--', 'foo.py', '--option1', '--option2']
    pre_opt, run_script, post_opt = resolve_argv()
    assert pre_opt == []
    assert run_script == 'foo.py'
    assert post_opt == ['--option1', '--option2']

    # Test case 7: Not .py or .pyw extension
    foo_full_path = os.path.join(this_script_dir, 'foo')
    sys.argv = ['uvr', '--', foo_full_path, '--option1', '--option2']
    pre_opt, run_script, post_opt = resolve_argv()
    assert pre_opt == ['--script']
    assert run_script == foo_full_path
    assert post_opt == ['--option1', '--option2']


def test_venv_python_at(tmp_path):
    venv_dir = tmp_path / '.venv'
    python = venv_dir / 'bin' / 'python'
    python.parent.mkdir(parents=True)
    python.write_text('')

    assert _venv_python_at(str(tmp_path)) == str(python)


def test_venv_python_at_windows(tmp_path):
    venv_dir = tmp_path / '.venv'
    python = venv_dir / 'Scripts' / 'python.exe'
    python.parent.mkdir(parents=True)
    python.write_text('')

    assert _venv_python_at(str(tmp_path)) == str(python)


def test_venv_python_at_missing(tmp_path):
    assert _venv_python_at(str(tmp_path)) is None


def test_find_venv_python_finds_dotvenv(tmp_path, monkeypatch):
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)

    project = tmp_path / 'project'
    project.mkdir()
    (project / 'pyproject.toml').write_text('')

    venv = project / '.venv' / 'bin'
    venv.mkdir(parents=True)
    python = venv / 'python'
    python.write_text('')

    script = project / 'script.py'
    script.write_text('')

    assert _find_venv_python(str(script)) == str(python)


def test_find_venv_python_stops_at_project_root(tmp_path, monkeypatch):
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)

    project = tmp_path / 'project'
    project.mkdir()
    (project / 'pyproject.toml').write_text('')

    # venv lives above the project root -> must not be found
    outside = tmp_path / '.venv' / 'bin'
    outside.mkdir(parents=True)
    (outside / 'python').write_text('')

    script = project / 'script.py'
    script.write_text('')

    assert _find_venv_python(str(script)) is None


def test_find_venv_python_respects_virtual_env(tmp_path, monkeypatch):
    venv = tmp_path / '.venv' / 'bin'
    venv.mkdir(parents=True)
    python = venv / 'python'
    python.write_text('')

    monkeypatch.setenv('VIRTUAL_ENV', str(tmp_path / '.venv'))

    assert _find_venv_python('/some/other/path') == str(python)


def test_is_offline_env():
    old = os.environ.get('UV_OFFLINE')
    try:
        os.environ['UV_OFFLINE'] = '1'
        assert _is_offline([]) is True

        os.environ['UV_OFFLINE'] = '0'
        assert _is_offline([]) is False

        del os.environ['UV_OFFLINE']
        assert _is_offline([]) is False
    finally:
        if old is None:
            os.environ.pop('UV_OFFLINE', None)
        else:
            os.environ['UV_OFFLINE'] = old


def test_is_offline_flag():
    assert _is_offline(['--offline']) is True
    assert _is_offline(['-v', '--offline']) is True
    assert _is_offline(['-v']) is False
    assert _is_offline([]) is False
