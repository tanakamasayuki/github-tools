#!/usr/bin/env bash
# Run all helper Python scripts and save their outputs to text files.

set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
cd "$script_dir"

python3 list_sibling_repos.py > list_sibling_repos.txt
python3 list_ignored_files.py > list_ignored_files.txt
python3 list_repo_changes.py > list_repo_changes.txt

echo "Outputs saved:"
echo "  list_sibling_repos.txt"
echo "  list_ignored_files.txt"
echo "  list_repo_changes.txt"
