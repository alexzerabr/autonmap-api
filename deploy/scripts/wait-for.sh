#!/usr/bin/env sh
# wait-for.sh

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 host:port [command...]" >&2
  exit 1
fi

TARGET="$1"
shift

HOST=$(printf "%s" "$TARGET" | cut -d: -f1)
PORT=$(printf "%s" "$TARGET" | cut -d: -f2)

echo "Waiting for $HOST:$PORT to be available..."
python3 - "$HOST" "$PORT" <<'PY'
import socket, sys, time
host, port = sys.argv[1], int(sys.argv[2])
while True:
    try:
        with socket.create_connection((host, port), timeout=3):
            break
    except Exception:
        time.sleep(1)
print(f"{host}:{port} is up")
PY

echo "$HOST:$PORT is up"

if [ $# -eq 0 ]; then
  exit 0
fi
exec "$@"
