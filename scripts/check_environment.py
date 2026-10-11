"""Report local development and hardware readiness without installing packages."""

from __future__ import annotations

import argparse
import ctypes
import csv
import importlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OPTIONAL_PACKAGES = {
    "torch": "PyTorch",
    "fastapi": "FastAPI",
    "PySide6": "PySide6",
}


def _memory_status() -> dict[str, float | int | str]:
    if os.name == "nt":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.dwLength = ctypes.sizeof(MemoryStatus)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        get_status = kernel32.GlobalMemoryStatusEx
        get_status.argtypes = [ctypes.POINTER(MemoryStatus)]
        get_status.restype = ctypes.c_int
        if not get_status(ctypes.byref(status)):
            return {"status": "unavailable", "error": "GlobalMemoryStatusEx failed"}
        return {
            "status": "available",
            "total_gib": round(status.ullTotalPhys / (1024**3), 2),
            "available_gib": round(status.ullAvailPhys / (1024**3), 2),
            "memory_load_percent": status.dwMemoryLoad,
        }

    return {"status": "unavailable", "reason": "RAM reporting is implemented for Windows"}


def _command_output(arguments: list[str], timeout: int = 10) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            arguments,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return {"status": "missing", "command": arguments[0]}
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Command timed out"}
    except OSError as error:
        return {"status": "error", "error": f"{type(error).__name__}: {error}"}

    if completed.returncode != 0:
        return {
            "status": "error",
            "return_code": completed.returncode,
            "error": (completed.stderr or completed.stdout).strip(),
        }
    return {"status": "available", "output": completed.stdout.strip()}


def _gpu_status() -> dict[str, Any]:
    result = _command_output(
        [
            "nvidia-smi",
            "--query-gpu=name,driver_version,memory.total,memory.free",
            "--format=csv,noheader,nounits",
        ]
    )
    if result["status"] != "available":
        return result

    rows = list(csv.reader(result["output"].splitlines(), skipinitialspace=True))
    if not rows or len(rows[0]) < 4:
        return {"status": "error", "error": "Unexpected nvidia-smi output"}
    name, driver, total_memory, free_memory = rows[0][:4]
    return {
        "status": "available",
        "name": name.strip(),
        "driver_version": driver.strip(),
        "total_vram_mib": int(total_memory.strip()),
        "free_vram_mib": int(free_memory.strip()),
    }


def _torch_status() -> dict[str, Any]:
    try:
        torch = importlib.import_module("torch")
    except ModuleNotFoundError as error:
        return {"status": "not_installed", "reason": error.name}
    except Exception as error:
        return {"status": "import_error", "error": f"{type(error).__name__}: {error}"}

    status: dict[str, Any] = {
        "status": "available",
        "version": torch.__version__,
        "cuda_build": torch.version.cuda,
        "cuda_available": False,
    }
    try:
        status["cuda_available"] = bool(torch.cuda.is_available())
        if status["cuda_available"]:
            properties = torch.cuda.get_device_properties(0)
            status["cuda_device"] = properties.name
            status["cuda_vram_mib"] = round(properties.total_memory / (1024**2))
    except Exception as error:
        status["cuda_check_error"] = f"{type(error).__name__}: {error}"
    return status


def _binary_status(name: str) -> dict[str, Any]:
    executable = shutil.which(name)
    if executable is None:
        return {"status": "missing"}
    result = _command_output([executable, "-version"])
    if result["status"] != "available":
        return result
    return {
        "status": "available",
        "path": executable,
        "version": result["output"].splitlines()[0],
    }


def _operating_system_status() -> dict[str, str]:
    name = platform.system()
    release = platform.release()
    version = platform.version()
    if os.name == "nt":
        windows_version = sys.getwindowsversion()
        build = windows_version.build
        release = "11" if build >= 22000 else "10" if build >= 10240 else release
        version = f"{windows_version.major}.{windows_version.minor}.{build}"
    return {"name": name, "release": release, "version": version}


def build_report() -> dict[str, Any]:
    sys.path.insert(0, str(PROJECT_ROOT))
    try:
        from voxsyn_ai import APP_NAME, __version__

        core = {"status": "available", "name": APP_NAME, "version": __version__}
    except Exception as error:
        core = {"status": "import_error", "error": f"{type(error).__name__}: {error}"}

    try:
        free_bytes = shutil.disk_usage(PROJECT_ROOT).free
        disk = {"status": "available", "free_gib": round(free_bytes / (1024**3), 2)}
    except OSError as error:
        disk = {"status": "error", "error": f"{type(error).__name__}: {error}"}

    dependencies: dict[str, Any] = {}
    for module_name, display_name in OPTIONAL_PACKAGES.items():
        try:
            version = importlib.metadata.version(module_name)
            dependencies[display_name] = {"status": "installed", "version": version}
        except importlib.metadata.PackageNotFoundError:
            dependencies[display_name] = {"status": "not_installed"}

    config_path = PROJECT_ROOT / "config" / "default.json"
    try:
        with config_path.open(encoding="utf-8") as config_file:
            config = json.load(config_file)
        memory_budget = config["runtime"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        memory_budget = {"status": "error", "error": f"{type(error).__name__}: {error}"}

    return {
        "application": {"name": "VoxSync Ai", "phase": 1},
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
        },
        "operating_system": _operating_system_status(),
        "system_memory": _memory_status(),
        "gpu": _gpu_status(),
        "pytorch": _torch_status(),
        "media_tools": {
            "ffmpeg": _binary_status("ffmpeg"),
            "ffprobe": _binary_status("ffprobe"),
        },
        "disk": disk,
        "dependencies": dependencies,
        "core_import": core,
        "memory_budget": memory_budget,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    arguments = parser.parse_args()
    report = build_report()

    if arguments.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{report['application']['name']} Phase {report['application']['phase']} environment")
        print(f"Python: {report['python']['version']} ({report['python']['executable']})")
        print(
            "OS: "
            f"{report['operating_system']['name']} "
            f"{report['operating_system']['release']}"
        )
        print(f"System memory: {report['system_memory']}")
        print(f"GPU: {report['gpu']}")
        print(f"PyTorch/CUDA: {report['pytorch']}")
        print(f"FFmpeg: {report['media_tools']['ffmpeg']}")
        print(f"ffprobe: {report['media_tools']['ffprobe']}")
        print(f"Project drive free space: {report['disk']}")
        print(f"Optional dependencies: {report['dependencies']}")
        print(f"Core import: {report['core_import']}")
        print(f"Configured memory budget: {report['memory_budget']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
