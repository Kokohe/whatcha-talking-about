#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$ROOT_DIR/runtime/pids"

if [[ ! -d "$PID_DIR" ]]; then
  echo "No active listeners found."
  exit 0
fi

FOUND=0
for pid_file in "$PID_DIR"/*.pid; do
  [[ -e "$pid_file" ]] || continue
  FOUND=1
  pid="$(<"$pid_file")"
  station="$(basename "$pid_file" .pid)"
  if kill -0 "$pid" >/dev/null 2>&1; then
    kill "$pid" >/dev/null 2>&1 || true
    echo "Stopped: $station (pid=$pid)"
  else
    echo "Already stopped: $station (pid=$pid)"
  fi
  rm -f "$pid_file"
done

if [[ "$FOUND" -eq 0 ]]; then
  echo "No active listeners found."
fi

