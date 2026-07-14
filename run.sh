#!/usr/bin/env bash
# IndustryIQ one-command setup + run.
#   ./run.sh          # build everything and serve on http://localhost:8000
#   ./run.sh dev      # backend on :8000 + Vite dev server on :5173 (hot reload)
set -euo pipefail
cd "$(dirname "$0")"

PY=.venv/bin/python
PIP=.venv/bin/pip

# --- python env ---------------------------------------------------------- #
if [ ! -x "$PY" ]; then
  echo "› creating venv"
  python3 -m venv .venv
  if ! "$PY" -m pip --version >/dev/null 2>&1; then
    echo "› bootstrapping pip"
    curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    "$PY" /tmp/get-pip.py >/dev/null
  fi
fi
echo "› installing backend deps"
"$PIP" install -q -r backend/requirements.txt

echo "› building seed + corpus"
"$PY" backend/scripts/build_seed.py
"$PY" backend/scripts/generate_corpus.py

# --- frontend ------------------------------------------------------------ #
if [ "${1:-}" = "dev" ]; then
  echo "› starting backend (:8000) and Vite dev (:5173)"
  "$PY" -m uvicorn backend.app.main:app --reload --port 8000 &
  BACK=$!
  (cd frontend && npm install && npm run dev)
  kill $BACK
else
  echo "› building frontend"
  (cd frontend && npm install && npm run build)
  echo "› serving on http://localhost:8000"
  exec "$PY" -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
fi
