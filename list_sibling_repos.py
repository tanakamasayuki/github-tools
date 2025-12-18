#!/usr/bin/env python3
"""List git repositories in sibling directories and show their remotes.

The script looks at the parent directory of this file (or a user provided one)
and inspects each immediate child directory. For each git repository it finds,
it prints the folder name and its remotes. When the folder name differs from
the default clone directory derived from a primary remote URL, a warning is
printed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a git command in cwd and return the completed process."""
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def is_git_repo(path: Path) -> bool:
    """Return True when path is inside a git work tree."""
    result = run_git(["rev-parse", "--is-inside-work-tree"], path)
    return result.returncode == 0 and result.stdout.strip() == "true"


def fetch_remotes(path: Path) -> dict[str, str]:
    """Return remotes with their fetch URLs."""
    result = run_git(["remote", "-v"], path)
    if result.returncode != 0:
        return {}

    remotes: dict[str, str] = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        name, url, direction = parts[0], parts[1], parts[2].strip("()")
        # Only keep the fetch URL for each remote.
        if direction == "fetch" and name not in remotes:
            remotes[name] = url
    return remotes


def repo_name_from_url(url: str) -> str:
    """Infer repository name from a git remote URL."""
    trimmed = url.rstrip("/")
    path_part = ""

    if "://" in trimmed:
        parsed = urlparse(trimmed)
        path_part = parsed.path.lstrip("/")
    else:
        # ssh style: git@github.com:user/repo.git
        if ":" in trimmed:
            path_part = trimmed.split(":", 1)[1]
        else:
            path_part = trimmed

    repo = path_part.rsplit("/", 1)[-1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    return repo


def primary_remote(remotes: dict[str, str]) -> tuple[str, str] | tuple[None, None]:
    """Pick a primary remote (origin first, otherwise alphabetical)."""
    if not remotes:
        return None, None
    if "origin" in remotes:
        return "origin", remotes["origin"]
    name = sorted(remotes.keys())[0]
    return name, remotes[name]


def list_sibling_repos(parent: Path) -> None:
    repos = []
    for entry in sorted(parent.iterdir(), key=lambda p: p.name.lower()):
        if not entry.is_dir():
            continue
        if is_git_repo(entry):
            repos.append(entry)

    for repo_dir in repos:
        remotes = fetch_remotes(repo_dir)
        remote_lines = []
        for name, url in sorted(
            remotes.items(), key=lambda item: (0 if item[0] == "origin" else 1, item[0])
        ):
            remote_lines.append(f"  - {name}: {url}")

        print(f"{repo_dir.name}")
        if remote_lines:
            print("\n".join(remote_lines))
        else:
            print("  (no remotes)")
        print()

        pri_name, pri_url = primary_remote(remotes)
        if pri_name and pri_url:
            expected = repo_name_from_url(pri_url)
            if expected and repo_dir.name != expected:
                warning = (
                    f"WARNING: folder '{repo_dir.name}' differs from default clone dir "
                    f"'{expected}' (remote: {pri_name})"
                )
                print(warning, file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List git repositories in sibling directories and show remotes."
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

    list_sibling_repos(parent)


if __name__ == "__main__":
    main()
