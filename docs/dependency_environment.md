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
- Before the PyTorch resolver dry run on 2026-10-11, available RAM was
  7.72 GiB, D: had 103.40 GiB free, and `nvidia-smi` reported 5920 MiB
  free VRAM.
- After the resolver dry run, available RAM was 7.61 GiB and D: still had
  103.40 GiB free; no large PyTorch/CUDA wheels were downloaded.
- PyTorch is absent from both `.venv` and `.venv310`; both environment
  reports accurately return `not_installed`.
- Git status before this task's documentation change was clean on
  `main`, tracking `origin/main`.
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
currently states that stable PyTorch requires Python 3.10 or later. Its
Windows/Pip/Python/CUDA 12.6 selector showed Stable 2.14.1 and this
command at the time of the check:

```powershell
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu126
```

The installed Python 3.10.11 meets PyTorch's documented base Python
minimum. A resolver-only, no-install check was run in `.venv310` using
the official CUDA 12.6 index:

```powershell
.\.venv310\Scripts\python.exe -m pip install --dry-run --no-cache-dir --report "$env:TEMP\voxsyn-pytorch-dry-run.json" torch torchvision --index-url https://download.pytorch.org/whl/cu126
```

The resolver identified `torch-2.14.1+cu126-cp310-cp310-win_amd64` and
`torchvision-0.29.1+cu126-cp310-cp310-win_amd64`, but **failed before
installation**. It rejected the `typing-extensions 4.16.0` wheel
metadata from the configured index as having an inconsistent project
name. The active pip was 23.0.1. Pip fell back to the source archive,
then could not find
`flit_core<4,>=3.11` for its isolated build environment in the
CUDA-only index. Pip exited with code 1. Some small package artifacts
were fetched for metadata/build preparation (133.2 kB Jinja2 wheel and
113.6 kB typing-extensions source archive); the large PyTorch/CUDA
wheels were not installed. No AI models were downloaded.

Per the stop-on-failure instruction, no alternate index, pip upgrade,
or retry was attempted. PyTorch remains absent from `.venv310` and
`.venv`; `torch.cuda.is_available()`, GPU tensor computation, and
PyTorch/driver CUDA compatibility remain **unverified**. The exact
wheel download size was not established because the resolver failed
before producing an install plan. No PyTorch installation was started.
Immediately after the resolver check, 7.61 GiB RAM was available and
103.40 GiB disk remained free. Recheck resources before any later
installation attempt.

## Resource-budget interpretation

The configured 10 GiB target and 12 GiB ceiling refer to **application
RAM**, not total system RAM. Neither limit has been validated by model
workloads. Available RAM was about 7.72 GiB immediately before and
7.61 GiB immediately after the resolver-only PyTorch check; no model
workload is recorded here.

The workspace preserves `LogoIcon.png`, `config/default.json`, and the
original `.venv`. The new `.venv310` is separately ignored by Git
patterns in `.gitignore`.
