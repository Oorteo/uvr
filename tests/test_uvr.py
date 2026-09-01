# SPDX-FileCopyrightText: 2026 Authors (see git history)
# SPDX-License-Identifier: MIT

import pytest
import sys

from uvr import *


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
