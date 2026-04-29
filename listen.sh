#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHANNELS_DIR="$ROOT_DIR/channels"
PID_DIR="$ROOT_DIR/runtime/pids"
LOG_DIR="$ROOT_DIR/runtime/logs"

mkdir -p "$CHANNELS_DIR" "$PID_DIR" "$LOG_DIR"

STATION_NAME=""
STATION_ID=""
STATION_URL=""
WHISPER_MODEL="small"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --station)
      STATION_NAME="${2:-}"
      shift 2
      ;;
    --station-id)
      STATION_ID="${2:-}"
      shift 2
      ;;
    --station-url)
      STATION_URL="${2:-}"
      shift 2
      ;;
    --model)
      WHISPER_MODEL="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: ./listen.sh --station \"Radio station name\"" >&2
      echo "   or: ./listen.sh --station-id \"stationId\" [--station \"Optional Label\"]" >&2
      echo "   or: ./listen.sh --station-url \"https://radio.garden/listen/.../<stationId>\" [--station \"Optional Label\"]" >&2
      echo "Optional: --model tiny|base|small|medium|large (default: small)" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$STATION_NAME" && -z "$STATION_ID" && -z "$STATION_URL" ]]; then
  echo "Usage: ./listen.sh --station \"Radio station name\"" >&2
  echo "   or: ./listen.sh --station-id \"stationId\" [--station \"Optional Label\"]" >&2
  echo "   or: ./listen.sh --station-url \"https://radio.garden/listen/.../<stationId>\" [--station \"Optional Label\"]" >&2
  echo "Optional: --model tiny|base|small|medium|large (default: small)" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but not found in PATH." >&2
  exit 1
fi

PYTHON_BIN="python3"
if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
fi

FFMPEG_BIN="${FFMPEG_BIN:-}"
if [[ -z "$FFMPEG_BIN" ]]; then
  if command -v ffmpeg >/dev/null 2>&1; then
    FFMPEG_BIN="$(command -v ffmpeg)"
  elif [[ -x "/opt/homebrew/bin/ffmpeg" ]]; then
    FFMPEG_BIN="/opt/homebrew/bin/ffmpeg"
  elif [[ -x "/usr/local/bin/ffmpeg" ]]; then
    FFMPEG_BIN="/usr/local/bin/ffmpeg"
  else
    echo "ffmpeg is required but not found in PATH." >&2
    echo "Install with: brew install ffmpeg" >&2
    exit 1
  fi
fi

RESOLVE_ARGS=()
if [[ -n "$STATION_NAME" ]]; then
  RESOLVE_ARGS+=(--station "$STATION_NAME")
fi
if [[ -n "$STATION_ID" ]]; then
  RESOLVE_ARGS+=(--station-id "$STATION_ID")
fi
if [[ -n "$STATION_URL" ]]; then
  RESOLVE_ARGS+=(--station-url "$STATION_URL")
fi

STATION_JSON="$("$PYTHON_BIN" "$ROOT_DIR/src/resolve_station.py" "${RESOLVE_ARGS[@]}")"
STATION_TITLE="$(printf "%s" "$STATION_JSON" | "$PYTHON_BIN" -c 'import json,sys; print(json.load(sys.stdin)["title"])')"
STATION_SLUG="$(printf "%s" "$STATION_JSON" | "$PYTHON_BIN" -c 'import json,sys; print(json.load(sys.stdin)["slug"])')"
STREAM_URL="$(printf "%s" "$STATION_JSON" | "$PYTHON_BIN" -c 'import json,sys; print(json.load(sys.stdin)["stream_url"])')"

PID_FILE="$PID_DIR/$STATION_SLUG.pid"
if [[ -f "$PID_FILE" ]]; then
  EXISTING_PID="$(<"$PID_FILE")"
  if kill -0 "$EXISTING_PID" >/dev/null 2>&1; then
    echo "Listener already running for '$STATION_TITLE' (pid=$EXISTING_PID)."
    exit 0
  fi
  rm -f "$PID_FILE"
fi

STATION_DIR="$CHANNELS_DIR/$STATION_SLUG"
LOG_FILE="$LOG_DIR/$STATION_SLUG.log"
FFMPEG_PID_FILE="$PID_DIR/$STATION_SLUG.ffmpeg.pid"
WORKER_PID_FILE="$PID_DIR/$STATION_SLUG.worker.pid"
mkdir -p "$STATION_DIR"

if [[ -f "$FFMPEG_PID_FILE" ]]; then
  OLD_PID="$(<"$FFMPEG_PID_FILE")"
  if kill -0 "$OLD_PID" >/dev/null 2>&1; then
    echo "Recorder already running for '$STATION_TITLE' (pid=$OLD_PID)."
    exit 0
  fi
  rm -f "$FFMPEG_PID_FILE"
fi

if [[ -f "$WORKER_PID_FILE" ]]; then
  OLD_PID="$(<"$WORKER_PID_FILE")"
  if kill -0 "$OLD_PID" >/dev/null 2>&1; then
    kill "$OLD_PID" >/dev/null 2>&1 || true
  fi
  rm -f "$WORKER_PID_FILE"
fi

nohup "$FFMPEG_BIN" \
  -hide_banner \
  -loglevel error \
  -i "$STREAM_URL" \
  -ac 1 \
  -ar 16000 \
  -c:a pcm_s16le \
  -f segment \
  -segment_time 30 \
  -reset_timestamps 1 \
  "$STATION_DIR/%06d.wav" >>"$LOG_FILE" 2>&1 &

LISTENER_PID="$!"
echo "$LISTENER_PID" > "$PID_FILE"
echo "$LISTENER_PID" > "$FFMPEG_PID_FILE"

nohup "$PYTHON_BIN" "$ROOT_DIR/src/transcribe_worker.py" \
  --channel-dir "$STATION_DIR" \
  --model "$WHISPER_MODEL" \
  >>"$LOG_FILE" 2>&1 &
WORKER_PID="$!"
echo "$WORKER_PID" > "$WORKER_PID_FILE"

echo "Started listener"
echo "  Station: $STATION_TITLE"
echo "  Recorder PID: $LISTENER_PID"
echo "  Worker PID: $WORKER_PID"
echo "  Python: $PYTHON_BIN"
echo "  Clips: $STATION_DIR"
echo "  Raw transcription: $STATION_DIR/raw-transcription.txt"
echo "  English translation: $STATION_DIR/translation.txt"
echo "Stop all listeners with: ./stop.sh"

