#!/usr/bin/env bash
# Build and upload mssql-sp-harness to PyPI.
#
# Usage:
#   ./scripts/publish-pypi.sh
#   ./scripts/publish-pypi.sh upload

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Building sdist and wheel"
python3 -m pip install -q build
python3 -m build

echo ""
ls -la dist/

echo "==> Validating artifacts (twine check)"
python3 -m pip install -q twine
python3 -m twine check dist/*

if [[ "${1:-}" == "upload" ]]; then
  python3 -m twine upload dist/*
else
  echo ""
  echo "To publish: ./scripts/publish-pypi.sh upload"
fi
