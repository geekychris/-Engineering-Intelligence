#!/usr/bin/env python3
"""Validate the generated Engineering Intelligence publication manifest."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import re
import sys


EXPECTED_SCHEMA_VERSION = 1
ALLOWED_BUILD_MODES = {"all", "html", "pdf", "validate"}
EXPECTED_ARTIFACTS = {
    "all": {"engineering-intelligence.html", "engineering-intelligence.pdf"},
    "validate": {"engineering-intelligence.html", "engineering-intelligence.pdf"},
    "html": {"engineering-intelligence.html"},
    "pdf": {"engineering-intelligence.pdf"},
}
FULL_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def digest(path: Path) -> str:
    hasher = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate(build_dir: Path, expected_commit: str | None = None) -> int:
    build_dir = build_dir.resolve()
    manifest_path = build_dir / "manifest.json"
    errors: list[str] = []

    if not manifest_path.is_file():
        print(f"ERROR: manifest was not found: {manifest_path}", file=sys.stderr)
        return 1

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: manifest could not be read: {exc}", file=sys.stderr)
        return 1

    if manifest.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        errors.append(
            "unsupported manifest schema_version: "
            f"{manifest.get('schema_version')!r}; expected {EXPECTED_SCHEMA_VERSION}"
        )

    build_mode = manifest.get("build_mode")
    if build_mode not in ALLOWED_BUILD_MODES:
        errors.append(f"invalid build_mode: {build_mode!r}")

    if manifest.get("title") != "Engineering Intelligence":
        errors.append("manifest title does not match the publication title")

    source_commit = manifest.get("source_commit")
    if not isinstance(source_commit, str) or not FULL_GIT_SHA_RE.fullmatch(source_commit):
        errors.append("source_commit must be a full 40-character lowercase Git SHA")
    elif expected_commit is not None and source_commit != expected_commit:
        errors.append(
            "source_commit does not match the expected release commit: "
            f"declared {source_commit!r}, expected {expected_commit!r}"
        )

    source_date_epoch = manifest.get("source_date_epoch")
    if not isinstance(source_date_epoch, int) or source_date_epoch < 0:
        errors.append("source_date_epoch must be a non-negative integer")

    publication_time = manifest.get("publication_time")
    if not isinstance(publication_time, str) or not publication_time:
        errors.append("publication_time must be a non-empty string")
    elif isinstance(source_date_epoch, int) and source_date_epoch >= 0:
        try:
            parsed_time = datetime.fromisoformat(publication_time)
        except ValueError:
            errors.append("publication_time must be a valid ISO-8601 timestamp")
        else:
            if parsed_time.tzinfo is None:
                errors.append("publication_time must include a timezone offset")
            else:
                expected_time = datetime.fromtimestamp(
                    source_date_epoch, timezone.utc
                )
                if parsed_time.astimezone(timezone.utc) != expected_time:
                    errors.append(
                        "publication_time does not match source_date_epoch: "
                        f"declared {publication_time!r}, expected "
                        f"{expected_time.isoformat()!r}"
                    )

    files = manifest.get("files")
    if not isinstance(files, list):
        errors.append("files must be an array")
        files = []

    declared_names: set[str] = set()
    for index, entry in enumerate(files):
        if not isinstance(entry, dict):
            errors.append(f"files[{index}] must be an object")
            continue

        name = entry.get("name")
        if not isinstance(name, str) or not name:
            errors.append(f"files[{index}].name must be a non-empty string")
            continue

        if name in declared_names:
            errors.append(f"duplicate artifact declaration: {name}")
            continue
        declared_names.add(name)

        if Path(name).name != name:
            errors.append(f"artifact name must not contain a path: {name}")
            continue

        path = build_dir / name
        if not path.is_file():
            errors.append(f"declared artifact is missing: {name}")
            continue

        declared_bytes = entry.get("bytes")
        actual_bytes = path.stat().st_size
        if declared_bytes != actual_bytes:
            errors.append(
                f"artifact size mismatch for {name}: "
                f"declared {declared_bytes!r}, actual {actual_bytes}"
            )

        declared_hash = entry.get("sha256")
        actual_hash = digest(path)
        if declared_hash != actual_hash:
            errors.append(
                f"artifact SHA-256 mismatch for {name}: "
                f"declared {declared_hash!r}, actual {actual_hash}"
            )

    if build_mode in EXPECTED_ARTIFACTS:
        expected_names = EXPECTED_ARTIFACTS[build_mode]
        if declared_names != expected_names:
            errors.append(
                f"artifact set for build_mode {build_mode!r} is invalid: "
                f"declared {sorted(declared_names)}, expected {sorted(expected_names)}"
            )

    diagrams_dir = build_dir / "figures" / "mermaid"
    actual_diagram_count = (
        len(list(diagrams_dir.glob("*.png"))) if diagrams_dir.is_dir() else 0
    )
    if manifest.get("diagram_count") != actual_diagram_count:
        errors.append(
            "diagram_count mismatch: "
            f"declared {manifest.get('diagram_count')!r}, "
            f"actual {actual_diagram_count}"
        )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        f"Validated publication manifest schema {EXPECTED_SCHEMA_VERSION}: "
        f"mode={build_mode}, artifacts={len(declared_names)}, "
        f"diagrams={actual_diagram_count}"
    )
    return 0


def main() -> int:
    build_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build")
    expected_commit = sys.argv[2] if len(sys.argv) > 2 else None
    return validate(build_dir, expected_commit)


if __name__ == "__main__":
    raise SystemExit(main())
