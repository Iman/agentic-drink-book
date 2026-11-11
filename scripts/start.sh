#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

for command in uv npm ollama curl; do
  command -v "$command" >/dev/null || { echo "Install $command before starting." >&2; exit 1; }
done
export NO_COLOR=1
export OLLAMA_HOST=127.0.0.1:11434
model="${1:-gemma3:4b}"
ollama_pid=""
web_pid=""
cleanup() {
  if [ -n "$web_pid" ]; then kill "$web_pid" 2>/dev/null || true; fi
  if [ -n "$ollama_pid" ]; then kill "$ollama_pid" 2>/dev/null || true; fi
}
trap cleanup EXIT
trap 'exit 130' INT TERM

uv sync --locked --color never
npm --prefix frontend ci --no-audit --no-fund
npm --prefix frontend run build
mkdir -p reports
if ! curl --fail --silent --max-time 2 http://127.0.0.1:11434/api/tags >/dev/null; then
  ollama serve >reports/ollama.log 2>&1 &
  ollama_pid=$!
  for ((attempt=0; attempt<30; attempt++)); do
    if curl --fail --silent --max-time 1 http://127.0.0.1:11434/api/tags >/dev/null; then break; fi
    if ! kill -0 "$ollama_pid" 2>/dev/null; then
      echo "Ollama could not start. See reports/ollama.log." >&2; exit 1
    fi
    sleep 1
  done
fi
curl --fail --silent --max-time 2 http://127.0.0.1:11434/api/tags >/dev/null || {
  echo "Ollama did not become ready. See reports/ollama.log." >&2; exit 1;
}
if ! ollama show "$model" >/dev/null 2>&1; then
  echo "The requested model is not installed. Run: ollama pull $model" >&2
  exit 1
fi
echo "Open http://127.0.0.1:8000. Press Ctrl+C to stop."
.venv/bin/agentic-web --provider local --model "$model" &
web_pid=$!
wait "$web_pid"
