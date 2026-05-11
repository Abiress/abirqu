#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=. python3 -m pytest -q "$@"
