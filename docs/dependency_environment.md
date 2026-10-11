# Phase 1 environment report

Audit date: 2026-10-11
Status: **PASS — Phase 1 environment and CUDA smoke verification complete.**

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
  3.10.11 runtime. It now contains pip 26.2.1 and CUDA-enabled PyTorch
  2.14.1+cu126. The original `.venv` was not modified.
- Total physical RAM: 15.71 GiB. Available RAM was 2.81 GiB before
  creating `.venv310`, 2.52 GiB immediately after, and 2.52 GiB during
  both environment-report runs. These are time-specific system values,
  not application peak-memory measurements.
- D: drive: 103.42 GiB free before venv creation and 103.40 GiB after.
- Immediately before PyTorch installation, available RAM was 7.20 GiB,
  D: had 103.40 GiB free, and `nvidia-smi` reported 5920 MiB free VRAM.
- After installing Torch and running CUDA tests, available RAM measured
  6.30 GiB initially and 6.38 GiB during the final report; D: had
  99.36 GiB free.
- PyTorch is installed only in `.venv310`; `.venv` remains Python 3.14.2
  with pip 25.3 and no Torch package.
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
- `.venv310\Scripts\python.exe -m pip check` — passed; no broken
  requirements.
- CUDA runtime test — passed: PyTorch `2.14.1+cu126`, CUDA build `12.6`,
  `torch.cuda.is_available() == True`, device `NVIDIA GeForce RTX 4050
  Laptop GPU`, and tensor `[1, 2, 3] * 2 + 1` evaluated on `cuda:0` to
  `[3, 5, 7]`.
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
minimum. The earlier pip 23.0.1 dry run failed on inconsistent
`typing-extensions` wheel metadata and missing `flit_core` from the
CUDA-only index.

Official pip documentation describes `--dry-run --report` as resolving
an install plan without installing packages. Pip was upgraded only
inside `.venv310`, using the official PyPI index:

```powershell
.\.venv310\Scripts\python.exe -m pip install --upgrade pip --index-url https://pypi.org/simple
```

It upgraded pip from 23.0.1 to 26.2.1 (1.8 MB downloaded). That alone
resolved the prior metadata/build-isolation failure. The original
`.venv` retains pip 25.3.

The official PyTorch Windows/Pip/Python/CUDA 12.6 selector showed Stable
2.14.1 and this command:

```powershell
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu126
```

For the minimal CUDA smoke test, the no-install resolver check omitted
`torchvision` because no vision package is needed for a tensor test:

```powershell
.\.venv310\Scripts\python.exe -m pip install --dry-run --no-cache-dir --report "$env:TEMP\voxsyn-pytorch-torchonly.json" torch --index-url https://download.pytorch.org/whl/cu126
```

The PyTorch CUDA 12.6 wheel index was used as the **single** package
index for Torch and dependency resolution. The pip upgrade used
`https://pypi.org/simple`. Dependencies resolved to package artifacts
hosted on PyPI's `files.pythonhosted.org` where applicable; no
`--extra-index-url` was used, avoiding ambiguous index priority.

The successful dry run selected:

| Package | Version |
|---|---:|
| torch | 2.14.1+cu126 |
| filelock | 3.32.3 |
| fsspec | 2026.7.0 |
| Jinja2 | 3.1.6 |
| MarkupSafe | 3.0.3 |
| mpmath | 1.3.0 |
| networkx | 3.4.2 |
| setuptools | 78.1.0 |
| sympy | 1.14.0 |
| typing_extensions | 4.16.0 |

HTTP `Content-Length` headers for the planned packages totaled about
2492.02 MiB; the Torch wheel was 2482.18 MiB. Pip reported downloading
the Torch wheel as 2602.8 MB. Installation succeeded in `.venv310`.
Free space on D: changed from 103.40 GiB before install to 99.36 GiB
after tests, a 4.04 GiB difference. No `torchvision`, NumPy, or AI
models were installed.

The runtime check produced:

```text
torch.__version__=2.14.1+cu126
torch.version.cuda=12.6
torch.cuda.is_available()=True
gpu=NVIDIA GeForce RTX 4050 Laptop GPU
tensor_device=cuda:0
tensor_result=[3, 5, 7]
```

PyTorch emitted a warning that NumPy is not installed when initializing
NumPy conversion support; the GPU computations still passed and
`pip check` found no broken requirements. NumPy was not added because
it is not required for the tested CUDA tensor operation.

## Resource-budget interpretation

The configured 10 GiB target and 12 GiB ceiling refer to **application
RAM**, not total system RAM. They have not been validated by AI model
workloads. Available system RAM was 7.20 GiB immediately before Torch
installation and 6.30 GiB after the CUDA tests. These are machine-level
readings, not a measurement of the application's peak RAM use.

The workspace preserves `LogoIcon.png`, `config/default.json`, and the
original `.venv`. The new `.venv310` is separately ignored by Git
patterns in `.gitignore`.
