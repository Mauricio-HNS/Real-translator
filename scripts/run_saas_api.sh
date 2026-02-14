#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt

HOST="${1:-0.0.0.0}"
PORT="${2:-8080}"

exec uvicorn saas_api.app:app --host "$HOST" --port "$PORT"
