# VoxSync Ai privacy

VoxSync Ai is designed for local media processing. User videos, audio,
voice references, transcripts, and generated outputs must remain on the
user's device; the application must not upload them, send them to remote
inference, or add telemetry or analytics.

Internet access may be used only when the user explicitly installs
software, downloads a model, or requests an update. Such downloads may
contact their package or model hosts. The Phase 1 environment and smoke
checks make no network requests and do not access user media.

Keep local model weights, caches, media, jobs, logs, credentials, and
generated benchmark files out of version control. Process only voice
samples the user owns or is authorized to use. Keep originals immutable
and write outputs to separate job directories. Later phases must add
safe path validation, explicit job cleanup, and user confirmation
before deleting job data.
