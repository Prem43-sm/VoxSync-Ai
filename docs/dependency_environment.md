# Phase 1 environment report

Audit date: 2026-10-11

## Observed environment

- Actual OS: Windows 11 Home Single Language, build 26300
  (`10.0.26300`). Python 3.10's `platform.release()` reports 10 on this
  system; the environment checker identifies Windows 11 from the OS
  build number instead.
- GPU: NVIDIA GeForce RTX 4050 Laptop GPU.
- NVIDIA driver: 610.88.
- GPU memory reported by `nvidia-smi`: 6141 MiB. Free VRAM was 5282 MiB
  during the first report and 5334 MiB during the follow-up.
- FFmpeg and ffprobe both execute successfully:
  `N-124716-g054dffd133-20260531`.
- Existing `.venv`: Python 3.14.2 with pip 25.3. It was not recreated,
  modified, or used to install packages.
- A separate `.venv310` was created from the already-installed Python
  3.10.11 runtime. It contains only pip 23.0.1 and occupies 18.31 MiB;
  no AI packages or models were installed.
- Total physical RAM: 15.71 GiB. Available RAM was 2.81 GiB before
  creating `.venv310`, 2.52 GiB immediately after, and 2.52 GiB during
  both environment-report runs. These are time-specific system values,
  not application peak-memory measurements.
- D: drive: 103.42 GiB free before venv creation and 103.40 GiB after.
- PyTorch is absent from both `.venv` and `.venv310`; both environment
  reports accurately return `not_installed`.
- Git metadata is absent at the project root, so a branch, tracked-file
  list, and dirty-worktree status cannot be reported.
- No AI models or model weights were downloaded.

## Phase 1 validation results

Commands run against both Python environments:

- `.venv\Scripts\python.exe scripts\check_environment.py` — completed;
  reported Python 3.14.2, Windows 11, GPU visibility, missing PyTorch,
  FFmpeg/ffprobe, disk space, and configured RAM limits.
- `.venv\Scripts\python.exe scripts\run_smoke_test.py` — passed:
  core import, FFmpeg execution, and ffprobe execution.
- `.venv310\Scripts\python.exe scripts\check_environment.py` —
  completed with equivalent results and correctly identifies Windows 11.
- `.venv310\Scripts\python.exe scripts\run_smoke_test.py` — passed
  the same three checks.
- Python compilation of `scripts` and `voxsyn_ai` passed in the existing
  Python 3.14 environment.
- Editor diagnostics for the three Python source files reported no
  errors.

The initial Python 3.10 environment report exposed that Python 3.10
reported the Windows 11 machine as Windows 10. The checker now detects
Windows 11 using the OS build number (Windows 11 builds start at 22000);
the check was rerun in both Python environments.

## PyTorch and CUDA status

The official [PyTorch installation guide](https://pytorch.org/get-started/locally/)
currently states that stable PyTorch requires Python 3.10 or later. The
installed Python 3.10.11 meets that base-version requirement. This does
not confirm a specific Windows CUDA wheel, driver/runtime compatibility,
or GPU execution.

CUDA verification remains **blocked**: PyTorch is not installed in
either environment, so `torch.cuda.is_available()` has not been run.
Installing CUDA-enabled PyTorch requires downloading PyTorch binaries
and CUDA runtime dependency packages. The exact download size depends on
the selected PyTorch/CUDA build and was not established; no package
download or installation was started. This is a multi-package,
multi-gigabyte installation that also needs additional disk space for
extracted packages and can consume RAM during installation/import. With
only about 2.5 GiB of system RAM available at the time of the checks,
installation and first import should wait until the user approves the
selected build and the machine has more free RAM. The 103.40 GiB free
disk space is ample for a separate test environment, but does not remove
the RAM constraint.

## Resource-budget interpretation

The configured 10 GiB target and 12 GiB ceiling refer to **application
RAM**, not total system RAM. Neither limit has been validated by model
workloads. The current system already had only about 2.5 GiB free during
checks, so keep setup lean and defer heavy package installation until
resources are available and the intended build is selected.

The workspace preserves `LogoIcon.png`, `config/default.json`, and the
original `.venv`. The new `.venv310` is separately ignored by Git
patterns in `.gitignore`.
