#!/usr/bin/env bash
set -euo pipefail

export API_URL="${API_URL:-http://localhost:8000}"

uvicorn src.interface.api.app:app --host 0.0.0.0 --port "${API_PORT:-8000}" &
api_pid=$!

streamlit run src/interface/streamlit_app/app.py \
  --server.address 0.0.0.0 \
  --server.port "${STREAMLIT_PORT:-8501}" \
  --browser.gatherUsageStats false &
ui_pid=$!

trap 'kill "$api_pid" "$ui_pid" 2>/dev/null || true' INT TERM

wait -n "$api_pid" "$ui_pid"
status=$?
kill "$api_pid" "$ui_pid" 2>/dev/null || true
wait "$api_pid" "$ui_pid" 2>/dev/null || true
exit "$status"
