#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
echo "=== Discord bot starting ==="

export PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD/.pythonlibs/lib/python3.12/site-packages${PYTHONPATH:+:$PYTHONPATH}"
exec python -u main.py