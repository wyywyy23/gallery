#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)"

cd "$SCRIPT_PATH"
python3 -c "import PIL" >/dev/null 2>&1 || {
  echo "Pillow is required. Install it with: python3 -m pip install Pillow"
  exit 1
}

python3 tools/rebuild_gallery.py "$@"
