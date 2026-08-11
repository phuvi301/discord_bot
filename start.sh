#!/bin/bash
echo "=== Bot starting ==="
export PYTHONPATH="$(pwd)/.pythonlibs/lib/python3.12/site-packages${PYTHONPATH:+:$PYTHONPATH}"
exec python -u main.py 2>&1
