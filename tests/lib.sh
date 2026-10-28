cd "$(dirname "$0")/.." || exit 1
PY=${PYTHON:-python3}
PORT=${PORT:-8765}
run() {
    echo
    echo "\$ python3 src/main.py $*"
    "$PY" -u src/main.py "$@" 2>&1
    echo "[код возврата: $?]"
}
start_server() {
    "$PY" -m http.server "$PORT" --directory tests/mock_repo \
        >/dev/null 2>&1 &
    SERVER_PID=$!
    sleep 1
}
stop_server() {
    kill "$SERVER_PID" 2>/dev/null
}
