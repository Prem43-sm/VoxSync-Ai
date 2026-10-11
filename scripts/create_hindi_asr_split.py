"""Create a content-deduplicated, deterministic Hindi ASR split manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "datasets" / "hindi_asr_11k"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "datasets" / "hindi_asr_11k_splits"
DEFAULT_EVALUATION_FRACTION = 0.1
DEFAULT_SEED = "2026-10-11"
SCRIPT_VERSION = 1


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_path(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


def _load_source(source: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    manifest_path = source / "manifest.json"
    with manifest_path.open("r", encoding="utf-8") as stream:
        source_manifest = json.load(stream)

    file_inventory = {
        entry["path"]: entry for entry in source_manifest.get("files", [])
    }
    groups: dict[str, dict[str, Any]] = {}
    split_counts: dict[str, int] = defaultdict(int)

    for split in ("train", "test"):
        metadata_path = source / split / "metadata.tsv"
        relative_metadata = metadata_path.relative_to(source).as_posix()
        _verify_source_file(metadata_path, relative_metadata, file_inventory)

        with metadata_path.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = csv.reader(stream, delimiter="\t", strict=True)
            if next(rows, None) != ["file_name", "text"]:
                raise ValueError(f"Unexpected TSV header: {metadata_path}")

            seen_names: set[str] = set()
            for line_number, row in enumerate(rows, start=2):
                if len(row) != 2 or not row[0] or not row[1].strip():
                    raise ValueError(
                        f"Malformed or empty row at {metadata_path}:{line_number}"
                    )

                file_name, transcript = row
                if (
                    Path(file_name).name != file_name
                    or "/" in file_name
                    or "\\" in file_name
                    or not file_name.startswith("common_voice_hi_")
                    or Path(file_name).suffix.lower() != ".mp3"
                ):
                    raise ValueError(f"Unsafe or unexpected audio name: {file_name}")
                if file_name in seen_names:
                    raise ValueError(
                        f"Duplicate filename in {split} metadata: {file_name}"
                    )
                seen_names.add(file_name)

                audio_path = source / split / "clips" / file_name
                relative_audio = audio_path.relative_to(source).as_posix()
                audio_digest = _verify_source_file(
                    audio_path, relative_audio, file_inventory
                )
                group = groups.setdefault(
                    audio_digest,
                    {
                        "transcript": transcript,
                        "sources": [],
                    },
                )
                if group["transcript"] != transcript:
                    raise ValueError(
                        "Identical audio has conflicting transcripts: "
                        f"{relative_audio}"
                    )
                group["sources"].append(
                    {
                        "published_split": split,
                        "audio_path": _relative_path(audio_path),
                    }
                )
                split_counts[split] += 1

        clips_dir = source / split / "clips"
        actual_names = {
            path.name for path in clips_dir.iterdir() if path.is_file()
        }
        expected_names = {
            Path(path).name
            for path in file_inventory
            if path.startswith(f"{split}/clips/")
        }
        if actual_names != expected_names:
            raise ValueError(f"Audio inventory differs from manifest in {clips_dir}")

    if split_counts != {"train": 9000, "test": 1000}:
        raise ValueError(f"Unexpected source row counts: {dict(split_counts)}")

    return groups, source_manifest


def _verify_source_file(
    path: Path,
    relative_path: str,
    file_inventory: dict[str, dict[str, Any]],
) -> str:
    entry = file_inventory.get(relative_path)
    if entry is None:
        raise ValueError(f"Source manifest has no entry for {relative_path}")
    if not path.is_file():
        raise FileNotFoundError(f"Source file is missing: {path}")
    if path.stat().st_size != entry["size_bytes"]:
        raise ValueError(f"Source file size differs from manifest: {relative_path}")
    digest = _sha256(path)
    if digest != entry["sha256"]:
        raise ValueError(f"Source SHA-256 differs from manifest: {relative_path}")
    return digest


def _record(
    audio_digest: str, group: dict[str, Any], assigned_split: str
) -> dict[str, Any]:
    preferred_source = "test" if assigned_split == "evaluation" else "train"
    sources = sorted(
        group["sources"],
        key=lambda source: (
            source["published_split"] != preferred_source,
            source["audio_path"],
        ),
    )
    return {
        "audio_path": sources[0]["audio_path"],
        "audio_sha256": audio_digest,
        "duplicate_count": len(sources),
        "published_splits": sorted(
            {source["published_split"] for source in sources}
        ),
        "source_audio_paths": sorted(
            source["audio_path"] for source in sources
        ),
        "text": group["transcript"],
    }


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(
                json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
            )


def create_split(
    source: Path,
    output: Path,
    evaluation_fraction: float,
    seed: str,
) -> dict[str, Any]:
    source = source.resolve()
    output = output.resolve()
    if source == output or source in output.parents or output in source.parents:
        raise ValueError("The output directory must be separate from the source.")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite output directory: {output}")
    if not 0 < evaluation_fraction < 1:
        raise ValueError("Evaluation fraction must be between 0 and 1.")
    if not seed:
        raise ValueError("Seed must not be empty.")

    groups, source_manifest = _load_source(source)
    if len(groups) < 2:
        raise ValueError("At least two unique audio groups are required.")

    evaluation_group_count = max(
        1, min(len(groups) - 1, int(len(groups) * evaluation_fraction + 0.5))
    )
    ranked_groups = sorted(
        groups,
        key=lambda audio_digest: (
            hashlib.sha256(f"{seed}:{audio_digest}".encode("utf-8")).hexdigest(),
            audio_digest,
        ),
    )
    evaluation_hashes = set(ranked_groups[:evaluation_group_count])

    training_records: list[dict[str, Any]] = []
    evaluation_records: list[dict[str, Any]] = []
    duplicate_groups = 0
    duplicate_rows = 0
    source_rows_by_assigned_split: dict[str, int] = {
        "training": 0,
        "evaluation": 0,
    }
    for audio_digest in sorted(groups):
        group = groups[audio_digest]
        assigned_split = (
            "evaluation" if audio_digest in evaluation_hashes else "training"
        )
        record = _record(audio_digest, group, assigned_split)
        target = (
            evaluation_records if assigned_split == "evaluation" else training_records
        )
        target.append(record)
        source_rows_by_assigned_split[assigned_split] += len(group["sources"])
        if len(group["sources"]) > 1:
            duplicate_groups += 1
            duplicate_rows += len(group["sources"]) - 1

    training_hashes = {record["audio_sha256"] for record in training_records}
    evaluation_hashes_written = {
        record["audio_sha256"] for record in evaluation_records
    }
    if training_hashes & evaluation_hashes_written:
        raise AssertionError("An exact audio hash appears in both split manifests.")

    temporary_output = Path(
        tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent)
    )
    try:
        train_path = temporary_output / "train.jsonl"
        evaluation_path = temporary_output / "evaluation.jsonl"
        _write_jsonl(train_path, training_records)
        _write_jsonl(evaluation_path, evaluation_records)
        output_inventory = []
        for path in (train_path, evaluation_path):
            output_inventory.append(
                {
                    "path": path.name,
                    "size_bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }
            )

        source_manifest_path = source / "manifest.json"
        split_manifest = {
            "format_version": 1,
            "generator_version": SCRIPT_VERSION,
            "source": {
                "name": source_manifest["dataset"]["name"],
                "url": source_manifest["dataset"]["source_url"],
                "revision": source_manifest["dataset"]["revision"],
                "manifest_sha256": _sha256(source_manifest_path),
            },
            "grouping": {
                "identity": "SHA-256 of complete audio file bytes",
                "near_duplicates_detected": False,
                "evaluation_fraction_of_unique_groups": evaluation_fraction,
                "seed": seed,
                "assignment_rule": (
                    "Rank unique audio SHA-256 values by "
                    "SHA-256(f'{seed}:{audio_sha256}'); assign the first "
                    "round(unique_group_count * evaluation_fraction) groups "
                    "to evaluation, with halves rounded up."
                ),
            },
            "counts": {
                "source_rows": sum(
                    len(group["sources"]) for group in groups.values()
                ),
                "unique_audio_groups": len(groups),
                "duplicate_audio_groups": duplicate_groups,
                "duplicate_rows_collapsed": duplicate_rows,
                "training_unique_audio_groups": len(training_records),
                "evaluation_unique_audio_groups": len(evaluation_records),
                "training_source_rows_represented": source_rows_by_assigned_split[
                    "training"
                ],
                "evaluation_source_rows_represented": source_rows_by_assigned_split[
                    "evaluation"
                ],
                "cross_split_exact_hashes": 0,
            },
            "limitations": [
                "Exact-byte SHA-256 grouping does not detect near-duplicate "
                "recordings or edited/re-encoded copies.",
                "Transcript agreement was required for all exact-duplicate "
                "audio groups; conflicting transcripts stop generation.",
                "This is a deterministic random-like split by unique audio "
                "content, not a speaker-disjoint split.",
            ],
            "files": output_inventory,
        }
        manifest_path = temporary_output / "split_manifest.json"
        with manifest_path.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(
                split_manifest,
                stream,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            stream.write("\n")

        if output.exists():
            raise FileExistsError(f"Refusing to overwrite output directory: {output}")
        temporary_output.rename(output)
    except BaseException:
        if temporary_output.exists():
            shutil.rmtree(temporary_output)
        raise

    return split_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--evaluation-fraction",
        type=float,
        default=DEFAULT_EVALUATION_FRACTION,
    )
    parser.add_argument("--seed", default=DEFAULT_SEED)
    args = parser.parse_args()

    result = create_split(
        args.source,
        args.output,
        args.evaluation_fraction,
        args.seed,
    )
    print(json.dumps(result["counts"], sort_keys=True))
    print(f"Output: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
