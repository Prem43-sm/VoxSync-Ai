# VoxSync Ai

VoxSync Ai is a local-first English-to-Hindi video dubbing studio. The
supplied project logo is [LogoIcon.png](./LogoIcon.png).

The project follows the six implementation phases in
[MASTER_PROJECT_PLAN.txt](./MASTER_PROJECT_PLAN.txt). Phase 1
(repository audit, environment, and feasibility) is complete, including
a verified CUDA tensor test. Phase 2 has not started and requires user
approval.

## Phase 1 quick checks

From PowerShell in the project directory:

```powershell
.\.venv310\Scripts\python.exe scripts\check_environment.py
.\.venv310\Scripts\python.exe scripts\run_smoke_test.py
.\.venv310\Scripts\python.exe -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

See [Windows setup](./docs/setup_windows.md),
[architecture](./docs/architecture.md), and
[privacy](./docs/privacy.md) for details. The existing `.venv` is Python
3.14.2 and remains separate and untouched; use `.venv310` for the
verified PyTorch CUDA environment. No AI inference models are installed.
