# Windows setup

## Requirements

- Windows 10/11.
- Python 3.10 is the initial target for the future model stack. Model
  dependencies must be checked before choosing a newer version.
- FFmpeg and ffprobe available on `PATH`.
- An NVIDIA driver is needed for NVIDIA GPU use. A CUDA Toolkit is not
  automatically required; follow the PyTorch installation instructions
  that match the selected PyTorch build.

The Phase 1 scripts use only the Python standard library. No AI models,
PyTorch packages, or other runtime dependencies are downloaded by these
steps.

## Create a separate model-compatible environment

Python 3.10 is already installed on the audited machine. To keep the
existing Python 3.14 environment unchanged, create a separate 3.10
environment in PowerShell from the project directory:

```powershell
py -3.10 -m venv .venv310
.\.venv310\Scripts\python.exe --version
.\.venv310\Scripts\python.exe scripts\check_environment.py
.\.venv310\Scripts\python.exe scripts\run_smoke_test.py
```

For the existing environment, continue to use its interpreter directly;
do not recreate it:

```powershell
.\.venv\Scripts\python.exe scripts\check_environment.py
.\.venv\Scripts\python.exe scripts\run_smoke_test.py
```

Do not overwrite an existing environment without checking which Python
it uses. In the audited workspace, `.venv` uses Python 3.14.2 and remains
untouched. `.venv310` uses Python 3.10.11 and contains only the default
pip installation; no PyTorch or AI model packages were installed. The
official [PyTorch install guide](https://pytorch.org/get-started/locally/)
currently lists Python 3.10 or later as the stable release minimum. This
does not verify that a particular CUDA wheel or future model package
works in this environment.

The official selector command and the failed, no-install dependency
resolution attempt are documented in
[`dependency_environment.md`](./dependency_environment.md). Do not
work around that failure by selecting a different CUDA index until the
package-index dependency-resolution issue is understood.

## Environment report

Run `scripts\check_environment.py` to report Python/OS, system RAM,
NVIDIA GPU and driver visibility, PyTorch/CUDA status, FFmpeg/ffprobe,
available project-drive space, optional dependencies, core import, and
the configured RAM budget. Add `--json` for machine-readable output.
Missing PyTorch or a missing GPU is reported as a status, not silently
treated as success.

Run `scripts\run_smoke_test.py` to check that the shared core imports
and that FFmpeg and ffprobe can execute. These checks do not process
media or download models.

## Storage and memory

Keep model weights, caches, input media, jobs, logs, and generated
outputs in ignored local directories. Model downloads are optional and
should be selected only after the Phase 2 requirements and licenses are
reviewed. VoxSync Ai targets peak application RAM below 10 GiB and must
stay under 12 GiB on the 16 GiB baseline machine; this target remains
unverified until real model jobs are measured. The environment report's
free disk-space value is informational; no complete model storage
estimate is available before model selection.

## Troubleshooting

- If FFmpeg or ffprobe is missing, install a Windows build and add its
  `bin` directory to `PATH`, then open a new PowerShell window.
- If `nvidia-smi` is missing, check the NVIDIA driver installation.
- If PyTorch is reported missing, Phase 1 has not installed it. Do not
  install an arbitrary CUDA Toolkit or model bundle; select compatible
  PyTorch/model versions and measure resource usage in Phase 2.
- See [the privacy policy](./privacy.md) before supplying media.
