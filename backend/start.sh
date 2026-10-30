#!/usr/bin/env bash
# Entrypoint for the FastAPI service.
#
# Starts the RQ worker alongside uvicorn and restarts it if it dies, so a
# transient Redis hiccup does not permanently kill background processing.
# If Redis is unreachable the worker exits immediately (the web service then
# processes jobs in-process) and the supervisor stops restarting it.

set -euo pipefail

WORKER_RESTART_DELAY="${WORKER_RESTART_DELAY:-5}"
WORKER_PID=""

shutdown() {
  # Forward termination to the worker so it can exit cleanly.
  if [[ -n "$WORKER_PID" ]] && kill -0 "$WORKER_PID" 2>/dev/null; then
    kill "$WORKER_PID" 2>/dev/null || true
  fi
}
trap shutdown TERM INT

supervise_worker() {
  while true; do
    python worker.py &
    WORKER_PID=$!
    # wait returns early on signal; `|| true` keeps set -e from killing us
    wait "$WORKER_PID" || true
    WORKER_PID=""

    if ! python -c "
from app.cache.redis_client import get_client
import sys
client = get_client()
sys.exit(0 if client.ping() else 1)
" 2>/dev/null; then
      echo "Redis still unreachable; not restarting the RQ worker." >&2
      break
    fi

    echo "RQ worker exited; restarting in ${WORKER_RESTART_DELAY}s..." >&2
    sleep "$WORKER_RESTART_DELAY"
  done
}

supervise_worker &

# Start the FastAPI web server in the foreground so the platform tracks it
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
