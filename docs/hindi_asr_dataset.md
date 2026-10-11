# Hindi ASR dataset preparation

Preparation date: 2026-10-11
Status: **Downloaded, pair-checked, and split by exact audio content for evaluation.**

## Source and license evidence

- Dataset: [dhruvkys/11k-asr](https://huggingface.co/datasets/dhruvkys/11k-asr)
- Pinned revision: `dc161f4fcf07cdfcd3852d9467e66c81964c5e52`
- The Hugging Face dataset API reported public, not gated, and
  `cardData.license: cc0-1.0`; its README front matter also declares
  `cc0-1.0`.
- The README describes the contents as a Hindi subset derived from
  Mozilla Common Voice and says the CC0-1.0 license is inherited from
  Common Voice. This is the dataset publisher's license declaration;
  upstream legal provenance was not independently audited. The
  repository has no standalone `LICENSE` file.
- No authentication was required or used.

## Download and storage

The source was cloned at the pinned revision with Git LFS smudge disabled,
then the LFS objects were checked out. No archive was downloaded or
extracted, and no Python packages, models, or model weights were
installed.

```powershell
$env:GIT_LFS_SKIP_SMUDGE = '1'
git clone --depth 1 --branch main `
  https://huggingface.co/datasets/dhruvkys/11k-asr `
  .\data\datasets\hindi_asr_11k
Remove-Item Env:GIT_LFS_SKIP_SMUDGE
git -C .\data\datasets\hindi_asr_11k lfs pull origin `
  dc161f4fcf07cdfcd3852d9467e66c81964c5e52
```

| Measurement | Result |
|---|---:|
| Train MP3s | 9,000 (255,357,800 bytes) |
| Test MP3s | 1,000 (31,812,540 bytes) |
| Total audio payload | 287,170,340 bytes (273.87 MiB) |
| Transcript TSVs | 1,465,601 bytes total |
| Hub-reported total file sizes | 288,644,238 bytes |
| Checked-out dataset files | 10,004 files; 288,644,480 bytes (275.40 MiB) |
| Observed D: free space before / after | 99.13 / 98.58 GiB |
| Observed D: disk-space change | 562.28 MiB, including the Git LFS object cache |
| Available system RAM before / after transfer | 5.36 / 4.75 GiB |

The checked-out total is 242 bytes larger than the Hub-reported sum; the
two root text files account for the difference. The dataset worktree
contains `.gitattributes`, `README.md`, the train/test metadata, and the
10,000 MP3 files. The local `manifest.json` inventories the 10,004
dataset files (excluding `.git` internals and itself) with per-file
sizes and SHA-256 checksums. The `data/` tree is Git-ignored; neither
the dataset nor its manifest is committed.

These system RAM readings are not application peak-memory measurements.
No AI model was loaded, so they do not establish the project's 10 GiB
RAM target or 12 GiB ceiling.

## Integrity checks

- Pinned local Git revision matches the inspected Hugging Face revision.
- Train and test each contain the expected number of MP3s and nonempty
  transcript rows. TSV columns are `file_name` and `text`.
- All 10,000 transcript filenames matched exactly one audio file; there
  were no unmatched transcript rows, orphan audio files, or duplicate
  transcript filenames within a split.
- All 10,000 transcript rows contained Devanagari text.
- All 10,000 MP3s had an ID3 or MPEG frame header signature.
- Three representative MP3s (including both splits and an overlapping
  clip) were inspected with `ffprobe` and fully decoded with FFmpeg.
  They were mono MP3; examples reported 32 kHz and 48 kHz sample rates.
- SHA-256 checksums were generated for every file in the downloaded
  dataset inventory.

### Evaluation leakage

**802 of the 1,000 published test filenames also occur in train, and
each shared audio file has the same SHA-256 hash and matching
transcript.** The published split is therefore not safe for evaluation.

The reproducible, derived manifests are in the separate ignored
`data/datasets/hindi_asr_11k_splits/` directory. Generate them with the
standard-library-only script:

```powershell
.\.venv310\Scripts\python.exe scripts\create_hindi_asr_split.py
```

The script verifies each source file against the SHA-256 inventory in
the original `manifest.json`; it does not modify the downloaded
dataset. It fails rather than overwriting an existing output directory.
The default command is intended for the initial generation; to reproduce
the files for comparison, pass a different, not-yet-existing `--output`
directory.
All rows with identical audio SHA-256 are collapsed to one unique
content group after confirming their transcripts agree. Groups are
ranked by `SHA-256("2026-10-11:" + audio_sha256)`; the first 10% (rounded
to the nearest whole group, halves up) are assigned to evaluation and
the rest to training. The seed is `2026-10-11`. The output manifest
records the rule, source revision and manifest checksum, counts, and
SHA-256 checksums of both JSONL files. Each JSONL item identifies its
audio path, transcript, content hash, duplicate count, and source paths.

Result for this snapshot:

| Measure | Result |
|---|---:|
| Published source rows | 10,000 |
| Unique exact-audio groups | 9,198 |
| Duplicate content groups | 802 |
| Redundant rows collapsed | 802 |
| Training groups / manifest entries | 8,278 |
| Evaluation groups / manifest entries | 920 |
| Source rows represented in training / evaluation | 8,992 / 1,008 |
| Exact audio hashes shared between derived training and evaluation | 0 |

Exact-byte SHA-256 grouping does **not** detect near-duplicate
recordings, including edited or re-encoded copies. This split is not
speaker-disjoint, and transcript agreement does not establish transcript
accuracy. Assess near-duplicates and speaker overlap before interpreting
later benchmark results. The derived manifests and the source dataset
remain ignored by Git.

Pairing and basic media integrity were checked; transcript accuracy,
clip duration, near-duplicate recordings, speaker overlap, and
suitability for the dubbing task were not assessed. The source is
read-speech ASR data, not validated dubbing evaluation material.

## Phase 2 boundary

This was a dataset preparation task only. No AI models or model weights
were downloaded, no inference or training was run, and Phase 2 model
benchmarking remains pending.
