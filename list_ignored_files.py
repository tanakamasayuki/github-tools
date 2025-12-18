#!/usr/bin/env python3
"""List ignored (excluded) files for sibling git repositories.

Scans the parent directory of this script (or a user-provided one) and for each
direct child that is a git repository, prints the ignored files detected by
`git ls-files --others -i --exclude-standard`.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def is_git_repo(path: Path) -> bool:
    result = run_git(["rev-parse", "--is-inside-work-tree"], path)
    return result.returncode == 0 and result.stdout.strip() == "true"


def list_ignored(path: Path) -> list[str]:
    result = run_git(["ls-files", "--others", "-i", "--exclude-standard"], path)
    if result.returncode != 0:
        sys.stderr.write(f"git ls-files failed in {path}: {result.stderr}")
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List ignored files in sibling git repositories."
    )
    parser.add_argument(
        "-p",
        "--parent",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Parent directory to scan (defaults to parent of this script).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    parent = args.parent.resolve()
    if not parent.is_dir():
        sys.stderr.write(f"Parent path is not a directory: {parent}\n")
        sys.exit(1)

    for entry in sorted(parent.iterdir(), key=lambda p: p.name.lower()):
        if not entry.is_dir():
            continue
        if not is_git_repo(entry):
            continue

        ignored = list_ignored(entry)
        print(entry.name)
        if ignored:
            for item in ignored:
                print(f"  - {item}")
        else:
            print("  (no ignored files)")
        print()


if __name__ == "__main__":
    main()
