"""Windows smoke test; run this file through uv, never through system Python."""

from __future__ import annotations

import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parent.parent.parent
LOG = Path(__file__).resolve().parent / "windows_smoke_test.log"


def write_log(text: str) -> None:
    with LOG.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
        stream.flush()


def run_uvr(entry_point: str, script: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    command = [
        "uv",
        "run",
        "--project",
        str(ROOT),
        entry_point,
        "--",
        str(script),
        *arguments,
    ]
    write_log("\n$ " + subprocess.list2cmdline(command) + "\n")
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=60,
    )
    write_log(f"exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}\n")
    return result


def check(condition: bool, message: str) -> None:
    status = "PASS" if condition else "FAIL"
    write_log(f"{status}: {message}\n")
    if not condition:
        raise AssertionError(message)


def main() -> int:
    LOG.unlink(missing_ok=True)
    write_log("uvr Windows smoke test\n")
    write_log(f"platform={platform.platform()}\n")
    write_log(f"sys.executable={sys.executable}\n")
    write_log(f"sys.prefix={sys.prefix}\n")
    write_log(f"cwd={Path.cwd()}\n")
    write_log(f"PATH={os.environ.get('PATH', '')}\n")

    check(sys.platform == "win32", "the test is running on Windows")
    uv_version = subprocess.run(
        ["uv", "--version"],
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    write_log(f"uv --version: exit={uv_version.returncode}, output={uv_version.stdout}{uv_version.stderr}\n")
    check(uv_version.returncode == 0, "uv is available on PATH")

    with tempfile.TemporaryDirectory(prefix="uvr smoke space ") as temporary_directory:
        test_directory = Path(temporary_directory)
        marker = test_directory / "marker.txt"
        child = test_directory / "child script.py"
        child.write_text(
            "from pathlib import Path\n"
            "import sys\n"
            "Path(sys.argv[1]).write_text(' '.join(sys.argv[2:]), encoding='utf-8')\n",
            encoding="utf-8",
        )

        debug = run_uvr("uvr", child, "-vv")
        check(debug.returncode == 0, "uvr -vv exits successfully")
        check("child script.py" in debug.stderr, "debug output preserves a spaced script path")

        console = run_uvr("uvr", child, str(marker), "console", "ok")
        check(console.returncode == 0, "uvr console entry point exits successfully")
        check(marker.read_text(encoding="utf-8") == "console ok", "console entry point runs the child")

        marker.unlink()
        gui = run_uvr("uvr-gui", child, str(marker), "gui", "ok")
        check(gui.returncode == 0, "uvr-gui entry point exits successfully")
        check(marker.read_text(encoding="utf-8") == "gui ok", "gui entry point runs the child")
        check("Traceback" not in gui.stderr, "gui entry point emits no traceback")

    write_log(f"completed={time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    print(f"PASS: Windows smoke test completed. Log: {LOG}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        write_log(f"FAIL: {type(error).__name__}: {error}\n")
        print(f"FAIL: {error}. Log: {LOG}", file=sys.stderr)
        raise SystemExit(1)