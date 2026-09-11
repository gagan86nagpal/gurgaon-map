#!/usr/bin/env bash
# Fast checks: data invariants (<1 s) + browser click-through test (~3 s). Used by the pre-commit hook.
set -e
cd "$(dirname "$0")/.."
python3 tests/test_data.py
python3 tests/test_click.py
