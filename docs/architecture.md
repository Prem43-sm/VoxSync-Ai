# VoxSync Ai architecture

## Current phase

Phase 1 (repository audit, environment, and feasibility) is complete.
Python 3.10.11, FFmpeg/ffprobe, and PyTorch CUDA tensor execution on the
RTX 4050 were verified in `.venv310`. The original Python 3.14.2 `.venv`
remains untouched. The current code is only a shared-core scaffold and
environment check: there is no dubbing pipeline or UI yet. Phase 2
requires user approval.

## Brand and local assets

- Application name: **VoxSync Ai**
- Supplied logo: [`LogoIcon.png`](../LogoIcon.png), retained at the project
  root for later desktop and web UI work.
- Default settings: [`config/default.json`](../config/default.json)

## Planned architecture

The desktop UI and local browser UI will call one shared Python core.
After model candidates are measured in Phase 2, the core will grow into
independent services for media handling, transcription, translation,
speech generation, timing, subtitles, rendering, and evaluation. A
FastAPI service will be introduced in Phase 5 as the shared interface
between that core and both UIs; it is not part of this phase.

The intended pipeline runs locally: validate media, extract audio,
transcribe and translate, let the user review dialogue, synthesize Hindi
audio, fit timing, optionally mix background audio, and write a new
output video. Original media must remain unchanged. Model downloads
require explicit setup and model/license verification; no model or
inference service is bundled or enabled by this scaffold.

## Hardware and resource policy

The baseline in the master plan is a Windows laptop with an RTX 4050
(6 GB VRAM) and 16 GB RAM. The recorded budget is a 10 GiB peak
application-RAM target and a 12 GiB ceiling. This is a design
constraint, not a measured claim: actual model workloads must be measured
in Phase 2. Model stages should run sequentially, use small/chunked
inputs, and provide a documented CPU or smaller-model fallback where
testing supports one.

The default config keeps processing local, prefers automatic device
selection, and limits concurrent GPU-heavy stages to one. These settings
do not imply that GPU inference is currently available: PyTorch/CUDA
must be installed and verified separately.

## Phase boundaries

1. **Phase 1:** audit, environment checks, local configuration, privacy
   and setup documentation.
2. **Phase 2:** compare candidate local models and record measured
   quality, runtime, memory, and license evidence.
3. **Phase 3:** implement the tested audio dubbing pipeline.
4. **Phase 4:** add video reconstruction, mixing, and subtitles.
5. **Phase 5:** build the local API and desktop/web interfaces.
6. **Phase 6:** improve quality, multi-speaker support, and release.

Only Phase 1 is in scope until the user approves the next phase.
