#!/usr/bin/env bash
set -euo pipefail

DIST_DIR="dist"
DIST="${DIST_DIR}/*"

echo "==> Cleaning previous builds..."
rm -rf "${DIST_DIR}" build/*.egg-info

echo "==> Installing build tools..."
pip install --upgrade build twine

echo "==> Building sdist and wheel..."
python -m build

echo "==> Checking package with twine..."
twine check ${DIST}

echo ""
echo "==> Built packages:"
ls -lh "${DIST_DIR}/"

echo ""
read -rp "==> Upload to PyPI? (y/N) " confirm
if [[ "${confirm}" =~ ^[Yy]$ ]]; then
    echo "==> Uploading to PyPI..."
    twine upload ${DIST}
    echo "==> Done."
else
    echo "==> Aborted."
fi
