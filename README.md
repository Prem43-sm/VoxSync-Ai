# VoxSync Ai

VoxSync Ai is a local-first English-to-Hindi video dubbing studio. The
supplied project logo is [LogoIcon.png](./LogoIcon.png).

The project follows the six implementation phases in
[MASTER_PROJECT_PLAN.txt](./MASTER_PROJECT_PLAN.txt). Only Phase 1
(repository audit, environment, and feasibility) is in progress. Model
benchmarking and the dubbing pipeline have not started.

## Phase 1 quick checks

From PowerShell in the project directory:

```powershell
.\.venv\Scripts\python.exe scripts\check_environment.py
.\.venv\Scripts\python.exe scripts\run_smoke_test.py
```

See [Windows setup](./docs/setup_windows.md),
[architecture](./docs/architecture.md), and
[privacy](./docs/privacy.md) for details. No AI models are installed by
these checks.
