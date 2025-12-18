#!/usr/bin/env python3
"""List repositories with uncommitted changes or untracked files.

Scans the parent directory of this script (or a specified one) and for each
direct child git repository prints the paths reported by
`git status --porcelain`, covering staged・未ステージ・未追跡のすべての変更を一覧表示します。
さらに、上位ブランチ（upstream）に対して未プッシュの差分（ahead/behind）も表示します。
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


def list_changes(path: Path) -> list[str]:
    """Return porcelain status lines for the repo (staged/unstaged/untracked)."""
    result = run_git(["status", "--porcelain"], path)
    if result.returncode != 0:
        sys.stderr.write(f"git status failed in {path}: {result.stderr}")
        return []
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def get_upstream(path: Path) -> str | None:
    """Return upstream ref (e.g., origin/main) or None if not set."""
    result = run_git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], path)
    if result.returncode != 0:
        return None
    ref = result.stdout.strip()
    return ref if ref else None


def ahead_behind(path: Path, upstream: str) -> tuple[int, int] | None:
    """Return (ahead, behind) counts versus upstream."""
    result = run_git(["rev-list", "--left-right", "--count", f"HEAD...{upstream}"], path)
    if result.returncode != 0:
        return None
    parts = result.stdout.strip().split()
    if len(parts) != 2:
        return None
    try:
        ahead, behind = int(parts[0]), int(parts[1])
        return ahead, behind
    except ValueError:
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List uncommitted changes in sibling git repositories."
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

        changes = list_changes(entry)
        print(entry.name)

        upstream = get_upstream(entry)
        if upstream:
            counts = ahead_behind(entry, upstream)
            if counts:
                ahead, behind = counts
                print(f"  upstream: {upstream} (ahead {ahead}, behind {behind})")
            else:
                print(f"  upstream: {upstream} (差分を取得できませんでした)")
        else:
            print("  upstream: (なし)")

        if changes:
            for line in changes:
                print(f"  - {line}")
        else:
            print("  (clean)")
        print()


if __name__ == "__main__":
    main()
