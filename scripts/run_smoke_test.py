"""Smoke-test the shared core import and FFmpeg/ffprobe discovery."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    try:
        from voxsyn_ai import APP_NAME, __version__
    except Exception as error:
        print(f"FAIL: core import failed: {type(error).__name__}: {error}")
        return 1

    print(f"PASS: imported {APP_NAME} core version {__version__}")
    failures = 0
    for name in ("ffmpeg", "ffprobe"):
        executable = shutil.which(name)
        if executable is None:
            print(f"FAIL: {name} was not found on PATH")
            failures += 1
            continue
        try:
            result = subprocess.run(
                [executable, "-version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            print(f"FAIL: {name} could not run: {type(error).__name__}: {error}")
            failures += 1
            continue
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            print(f"FAIL: {name} returned {result.returncode}: {detail}")
            failures += 1
            continue
        version = result.stdout.splitlines()[0] if result.stdout else "version output unavailable"
        print(f"PASS: {name} is runnable ({version})")

    if failures:
        print(f"Smoke test failed with {failures} check(s).")
        return 1
    print("Smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
