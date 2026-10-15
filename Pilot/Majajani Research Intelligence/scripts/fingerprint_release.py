#!/usr/bin/env python3
"""Create or verify SHA-256 fingerprints for the repository release files."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "integrity" / "SHA256SUMS"
INCLUDE_DIRS = ("manuscript", "scripts", "visuals", "integrity")
ROOT_FILES = (".gitignore", "CITATION.cff", "Makefile", "README.md", "RIGHTS.md")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def release_files() -> list[Path]:
    files = [ROOT / name for name in ROOT_FILES if (ROOT / name).is_file()]
    for directory in INCLUDE_DIRS:
        base = ROOT / directory
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path == MANIFEST:
                continue
            if "__pycache__" in path.parts or path.suffix in {".pyc", ".tmp", ".bak"}:
                continue
            files.append(path)
    return sorted(set(files), key=lambda p: p.relative_to(ROOT).as_posix())


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def write_manifest() -> int:
    records = [f"{digest(path)}  {path.relative_to(ROOT).as_posix()}" for path in release_files()]
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    temporary = MANIFEST.with_suffix(".tmp")
    temporary.write_text("\n".join(records) + "\n", encoding="utf-8")
    os.replace(temporary, MANIFEST)
    print(f"Wrote SHA-256 baseline for {len(records)} files: {MANIFEST.relative_to(ROOT)}")
    print("Keep an independent copy of this manifest (or sign it) to detect replacement of both file and baseline.")
    return 0


def verify_manifest() -> int:
    if not MANIFEST.is_file():
        print("Missing integrity/SHA256SUMS. Create an initial baseline with --write.", file=sys.stderr)
        return 2
    expected: dict[str, str] = {}
    for line_number, line in enumerate(MANIFEST.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value, relative = line.split("  ", 1)
        except ValueError:
            print(f"Malformed manifest line {line_number}", file=sys.stderr)
            return 2
        if not SHA256_RE.match(value):
            print(f"Invalid SHA-256 on manifest line {line_number}", file=sys.stderr)
            return 2
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            print(f"Unsafe manifest path on line {line_number}: {relative}", file=sys.stderr)
            return 2
        if relative in expected:
            print(f"Duplicate manifest path: {relative}", file=sys.stderr)
            return 2
        expected[relative] = value

    current_paths = {path.relative_to(ROOT).as_posix(): path for path in release_files()}
    failures: list[str] = []
    for relative, value in expected.items():
        path = current_paths.get(relative)
        if path is None:
            failures.append(f"MISSING {relative}")
        elif digest(path) != value:
            failures.append(f"CHANGED {relative}")
    for relative in sorted(set(current_paths) - set(expected)):
        failures.append(f"UNFINGERPRINTED {relative}")

    if failures:
        print("Integrity verification FAILED:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print(f"Integrity verification passed: {len(expected)} files match the SHA-256 baseline.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="Create/refresh the baseline after an approved release change")
    group.add_argument("--verify", action="store_true", help="Check files against the existing baseline")
    args = parser.parse_args()
    return write_manifest() if args.write else verify_manifest()


if __name__ == "__main__":
    raise SystemExit(main())
