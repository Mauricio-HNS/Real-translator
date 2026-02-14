#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/Mauricio-HNS/Real-translator.git}"
TARGET_DIR="${RT_DIR:-$HOME/Real-translator}"
HOST="${RT_HOST:-127.0.0.1}"
PORT="${RT_PORT:-7892}"

if ! command -v git >/dev/null 2>&1; then
  echo "Erro: git não encontrado. Instale o git e tente novamente."
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Erro: python3 não encontrado. Instale Python 3.10+ e tente novamente."
  exit 1
fi

PY_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PY_MAJOR="${PY_VER%%.*}"
PY_MINOR="${PY_VER##*.}"
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
  echo "Erro: Python $PY_VER detectado. Use Python 3.10 ou superior."
  exit 1
fi

if [ ! -d "$TARGET_DIR/.git" ]; then
  echo "Clonando repositório em: $TARGET_DIR"
  git clone "$REPO_URL" "$TARGET_DIR"
else
  echo "Repositório já existe em $TARGET_DIR. Atualizando..."
  git -C "$TARGET_DIR" pull --ff-only
fi

cd "$TARGET_DIR"

if [ ! -d ".venv" ]; then
  echo "Criando ambiente virtual..."
  python3 -m venv .venv
fi

echo "Ativando ambiente virtual e instalando dependências..."
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Iniciando Tradutor em Tempo Real..."
echo "URL: http://$HOST:$PORT"
echo "Para parar: Ctrl + C"
echo ""
python main_web.py --host "$HOST" --port "$PORT"
