#!/bin/zsh
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate

pip install -r requirements-build.txt

pyinstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "RealTranslator" \
  --collect-all gradio \
  main_desktop.py

echo "Build complete: dist/RealTranslator.app"
