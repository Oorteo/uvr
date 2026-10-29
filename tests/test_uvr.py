# SPDX-FileCopyrightText: 2026 Authors (see git history)
# SPDX-License-Identifier: MIT

import os
import sys
from types import SimpleNamespace

import pytest
import uvr.uvr as uvr_module

from uvr import (
    _find_venv_python,
    _resolve_prog_args,
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


def test_find_venv_python_active_environment_has_priority(tmp_path, monkeypatch):
    project = tmp_path / 'plugin'
    project_python = project / '.venv' / 'bin' / 'python'
    project_python.parent.mkdir(parents=True)
    project_python.write_text('')

    active_python = tmp_path / 'host-venv' / 'bin' / 'python'
    active_python.parent.mkdir(parents=True)
    active_python.write_text('')
    monkeypatch.setenv('VIRTUAL_ENV', str(active_python.parent.parent))

    assert _find_venv_python(str(project)) == str(active_python)


def test_resolve_poetry_script_uses_venv_without_calling_uv(tmp_path, monkeypatch):
    project = tmp_path / 'poetry-plugin'
    python = project / '.venv' / 'bin' / 'python'
    python.parent.mkdir(parents=True)
    python.write_text('')
    script = project / 'plugin.py'
    script.write_text('')
    (project / 'pyproject.toml').write_text('[tool.poetry]\n')
    (project / 'poetry.lock').write_text('')
    (project / 'uv.lock').write_text('')
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)

    assert _resolve_prog_args(str(script), [], ['--flag']) == [
        str(python), str(script), '--flag'
    ]


def test_resolve_script_uses_active_venv_before_plugin_venv(tmp_path, monkeypatch):
    project = tmp_path / 'plugin'
    local_python = project / '.venv' / 'bin' / 'python'
    local_python.parent.mkdir(parents=True)
    local_python.write_text('')
    script = project / 'plugin.py'
    script.write_text('')
    (project / 'pyproject.toml').write_text('[project]\nname = "plugin"\n')

    active_python = tmp_path / 'host-venv' / 'bin' / 'python'
    active_python.parent.mkdir(parents=True)
    active_python.write_text('')
    monkeypatch.setenv('VIRTUAL_ENV', str(active_python.parent.parent))

    assert _resolve_prog_args(str(script), [], []) == [str(active_python), str(script)]


def test_resolve_uv_script_without_venv_keeps_bootstrap_behavior(tmp_path, monkeypatch):
    project = tmp_path / 'uv-plugin'
    project.mkdir()
    (project / 'pyproject.toml').write_text('[project]\nname = "plugin"\n')
    (project / 'uv.lock').write_text('')
    script = project / 'plugin.py'
    script.write_text(
        '# /// script\n# requires-python = ">=3.12"\n'
        '# dependencies = ["httpx"]\n# ///\n'
    )
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)

    assert _resolve_prog_args(str(script), [], []) == [
        'uv', 'run', str(script)
    ]


def test_resolve_inline_script_metadata_takes_precedence_over_project_venv(
    tmp_path, monkeypatch
):
    project = tmp_path / 'uv-plugin'
    project.mkdir()
    (project / 'pyproject.toml').write_text('[project]\nname = "plugin"\n')
    (project / '.venv' / 'bin').mkdir(parents=True)
    (project / '.venv' / 'bin' / 'python').write_text('')
    script = project / 'plugin.py'
    script.write_text('# /// script\n# dependencies = ["httpx"]\n# ///\n')
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)

    assert _resolve_prog_args(str(script), [], []) == [
        'uv', 'run', str(script)
    ]


def test_resolve_project_without_venv_fails_instead_of_using_uv(
    tmp_path, monkeypatch
):
    project = tmp_path / 'new-plugin'
    project.mkdir()
    (project / 'pyproject.toml').write_text('[project]\nname = "plugin"\n')
    script = project / 'plugin.py'
    script.write_text('')
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)

    with pytest.raises(ValueError, match='no usable .venv'):
        _resolve_prog_args(str(script), [], [])


def test_resolve_script_without_project_uses_configured_system_python(
    tmp_path, monkeypatch
):
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)
    system_python = str(tmp_path / 'python3')
    monkeypatch.setenv('UVR_SYSTEM_PYTHON', system_python)
    script = tmp_path / 'standalone.py'
    script.write_text('')

    assert _resolve_prog_args(str(script), [], ['--flag']) == [
        system_python, str(script), '--flag'
    ]


def test_resolve_poetry_without_venv_fails_instead_of_using_uv(tmp_path, monkeypatch):
    project = tmp_path / 'poetry-plugin'
    project.mkdir()
    (project / 'pyproject.toml').write_text('[tool.poetry]\n')
    script = project / 'plugin.py'
    script.write_text('')
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)

    with pytest.raises(ValueError, match='Poetry project has no usable .venv'):
        _resolve_prog_args(str(script), [], [])


def test_resolve_program_uses_only_project_venv_bin(tmp_path, monkeypatch):
    project = tmp_path / 'plugin'
    program = project / '.venv' / 'bin' / 'plugin-command'
    program.parent.mkdir(parents=True)
    program.write_text('#!/bin/sh\n')
    program.chmod(0o755)
    (project / '.venv' / 'bin' / 'python').write_text('')
    (project / 'pyproject.toml').write_text('[project]\nname = "plugin"\n')
    (project / 'uv.lock').write_text('')
    unrelated = tmp_path / 'bin' / 'plugin-command'
    unrelated.parent.mkdir()
    unrelated.write_text('#!/bin/sh\n')
    unrelated.chmod(0o755)
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)

    assert _resolve_prog_args('plugin-command', [], ['arg'], cwd=str(project)) == [
        str(program), 'arg'
    ]


def test_resolve_program_falls_back_to_path(tmp_path, monkeypatch):
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    program = bin_dir / 'plugin-command'
    program.write_text('#!/bin/sh\n')
    program.chmod(0o755)
    monkeypatch.setenv('PATH', str(bin_dir))

    assert _resolve_prog_args('plugin-command', [], ['arg'], cwd=str(tmp_path)) == [
        str(program), 'arg'
    ]


def test_resolve_executable_program_by_path_does_not_treat_it_as_python_script(
    tmp_path, monkeypatch
):
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)
    project = tmp_path / 'project'
    program = project / '.venv' / 'bin' / 'plugin-command'
    program.parent.mkdir(parents=True)
    program.write_text('#!/usr/bin/python3\n')
    program.chmod(0o755)
    (program.parent / 'python').write_text('')

    assert _resolve_prog_args(str(program), [], [], cwd=str(project)) == [
        str(program)
    ]


def test_resolve_program_uses_active_venv_before_plugin_venv(tmp_path, monkeypatch):
    project = tmp_path / 'plugin'
    project_program = project / '.venv' / 'bin' / 'tool'
    project_program.parent.mkdir(parents=True)
    project_program.write_text('#!/bin/sh\n')
    project_program.chmod(0o755)
    (project / '.venv' / 'bin' / 'python').write_text('')
    (project / 'pyproject.toml').write_text('[project]\nname = "plugin"\n')

    active_program = tmp_path / 'host-venv' / 'bin' / 'tool'
    active_program.parent.mkdir(parents=True)
    active_program.write_text('#!/bin/sh\n')
    active_program.chmod(0o755)
    (active_program.parent / 'python').write_text('')
    monkeypatch.setenv('VIRTUAL_ENV', str(active_program.parent.parent))

    assert _resolve_prog_args('tool', [], [], cwd=str(project)) == [str(active_program)]


def test_resolve_program_without_venv_fails_offline(tmp_path, monkeypatch):
    project = tmp_path / 'uv-plugin'
    project.mkdir()
    (project / 'pyproject.toml').write_text('[project]\nname = "plugin"\n')
    (project / 'uv.lock').write_text('')
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)
    monkeypatch.setenv('PATH', '')

    with pytest.raises(ValueError, match='Offline mode requires a usable project .venv'):
        _resolve_prog_args('pytest', ['--offline'], ['-q'], cwd=str(project))


def test_resolve_command_without_project_fails_offline(tmp_path, monkeypatch):
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)
    monkeypatch.setenv('PATH', '')

    with pytest.raises(ValueError, match='Offline mode requires a usable project .venv'):
        _resolve_prog_args('pytest', ['--offline'], ['-q'], cwd=str(tmp_path))


def test_resolve_script_without_venv_fails_when_uv_offline_env_is_set(tmp_path, monkeypatch):
    project = tmp_path / 'uv-plugin'
    project.mkdir()
    (project / 'pyproject.toml').write_text('[project]\nname = "plugin"\n')
    script = project / 'plugin.py'
    script.write_text('')
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)
    monkeypatch.setenv('UV_OFFLINE', '1')

    with pytest.raises(ValueError, match='Offline mode requires a usable project .venv'):
        _resolve_prog_args(str(script), [], [], cwd=str(project))


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


def test_default_python_uses_project_venv(tmp_path, monkeypatch):
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)
    monkeypatch.setenv('UVR_SYSTEM_PYTHON', '/system/python3')
    python = tmp_path / '.venv' / 'bin' / 'python'
    python.parent.mkdir(parents=True)
    python.write_text('')

    assert uvr_module._resolve_default_python_args(str(tmp_path)) == [str(python)]


def test_default_python_rejects_project_without_venv(tmp_path, monkeypatch):
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)
    (tmp_path / 'pyproject.toml').write_text('[project]\nname = "plugin"\n')

    with pytest.raises(ValueError, match='no usable .venv'):
        uvr_module._resolve_default_python_args(str(tmp_path))


def test_main_without_arguments_starts_system_python(tmp_path, monkeypatch):
    system_python = str(tmp_path / 'python3')
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)
    monkeypatch.setenv('UVR_SYSTEM_PYTHON', system_python)
    monkeypatch.setattr(uvr_module.sys, 'argv', ['uvr'])
    monkeypatch.setattr(uvr_module, '_owns_console', lambda: True)
    calls = []
    monkeypatch.setattr(
        uvr_module.subprocess,
        'run',
        lambda args, **kwargs: calls.append((args, kwargs)) or SimpleNamespace(returncode=0),
    )

    with pytest.raises(SystemExit) as exit_info:
        uvr_module.main()

    assert exit_info.value.code == 0
    assert calls == [([system_python], {'check': False})]


@pytest.mark.parametrize('help_option', ['-h', '--help'])
def test_main_help_options_exit_successfully(help_option, monkeypatch, capsys):
    monkeypatch.setattr(uvr_module.sys, 'argv', ['uvr', help_option])
    monkeypatch.setattr(
        uvr_module.subprocess,
        'run',
        lambda *args, **kwargs: pytest.fail('help must not launch a child process'),
    )

    with pytest.raises(SystemExit) as exit_info:
        uvr_module.main()

    assert exit_info.value.code == 0
    assert 'Usage:' in capsys.readouterr().out


@pytest.mark.parametrize(
    ('shebang', 'expected_prefix'),
    [
        ('#!/usr/bin/env -S poetry run python', ['poetry', 'run', 'python']),
        ('#!/usr/bin/env -S conda run -n plugin python',
         ['conda', 'run', '-n', 'plugin', 'python']),
        ('#!/usr/bin/env -S uv run --script', ['uv', 'run', '--script']),
    ],
)
def test_manager_shebang_takes_precedence_over_project_venv(
    tmp_path, monkeypatch, shebang, expected_prefix
):
    project = tmp_path / 'plugin'
    project.mkdir()
    (project / '.venv' / 'bin').mkdir(parents=True)
    (project / '.venv' / 'bin' / 'python').write_text('')
    script = project / 'plugin.py'
    script.write_text(f'{shebang}\nprint("hello")\n')
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)

    assert _resolve_prog_args(str(script), [], ['arg']) == [
        *expected_prefix, str(script), 'arg'
    ]


def test_explicit_uv_script_option_overrides_manager_shebang(tmp_path, monkeypatch):
    script = tmp_path / 'plugin.py'
    script.write_text('#!/usr/bin/env -S poetry run python\nprint("hello")\n')
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)

    assert _resolve_prog_args(str(script), ['--script'], ['arg']) == [
        'uv', 'run', '--script', str(script), 'arg'
    ]
