#!/usr/bin/env bash
# memory_guard.sh — watchdog that kills agent-spawned descendants when
# their aggregate RSS exceeds a threshold. Only descendants of the
# Codex main process (or an explicit --root-pid) are touched.
set -u

THRESHOLD_GB=400
INTERVAL=5
ROOT_PID=""
TAG="${MEMORY_GUARD_TAG:-default}"
PID_FILE="/tmp/memory-guard-${USER}-${TAG}.pid"
LOG_FILE="/tmp/memory-guard-${USER}-${TAG}.log"

usage() {
    cat <<EOF
Usage: $0 <start|stop|status|check> [--threshold GB] [--interval SEC] [--root-pid PID] [--tag NAME]

Commands:
  start   Launch the guard daemon in the background
  stop    Stop the guard daemon
  status  Print daemon state + tail of log
  check   One-shot: print current total-RSS under root, no killing

Options:
  --threshold GB   Aggregate RSS kill threshold in GB (default: ${THRESHOLD_GB})
  --interval SEC   Poll interval in seconds (default: ${INTERVAL})
  --root-pid PID   Root PID whose descendants to watch (default: auto-detect Codex ancestor)
  --tag NAME       Instance tag so multiple guards can coexist (default: "default")

Files:
  \$PID_FILE  ${PID_FILE}
  \$LOG_FILE  ${LOG_FILE}
EOF
}

log() { echo "[$(date -Iseconds)] $*" >> "$LOG_FILE"; }

# Climb parent chain looking for a process whose comm is exactly
# "codex" (the Codex binary). Path-based matches on
# ".codex/..." would false-positive on any ancestor shell that
# inherited such a cmdline, so we check comm only.
detect_root() {
    local pid=$PPID
    local i=0
    while [[ "$pid" -gt 1 && "$i" -lt 20 ]]; do
        local comm=""
        comm=$(cat "/proc/$pid/comm" 2>/dev/null || true)
        if [[ "$comm" == "codex" ]]; then
            echo "$pid"
            return 0
        fi
        local ppid
        ppid=$(awk '{print $4}' "/proc/$pid/stat" 2>/dev/null || echo 0)
        [[ -z "$ppid" || "$ppid" -le 1 ]] && break
        pid=$ppid
        i=$((i + 1))
    done
    echo "$PPID"
    return 0
}

get_descendants() {
    local root=$1
    local queue=("$root")
    while [[ ${#queue[@]} -gt 0 ]]; do
        local p=${queue[0]}
        queue=("${queue[@]:1}")
        local children
        children=$(pgrep -P "$p" 2>/dev/null || true)
        for c in $children; do
            echo "$c"
            queue+=("$c")
        done
    done
}

rss_kb_of() {
    awk '/^VmRSS:/ {print $2; exit}' "/proc/$1/status" 2>/dev/null || true
}

comm_of() {
    cat "/proc/$1/comm" 2>/dev/null || echo "?"
}

scan_once() {
    local root=$1 self=$2
    local total_kb=0
    local entries=()
    while IFS= read -r pid; do
        [[ -z "$pid" || "$pid" == "$self" || "$pid" == "$root" ]] && continue
        local rss
        rss=$(rss_kb_of "$pid")
        [[ -z "$rss" || "$rss" == 0 ]] && continue
        total_kb=$((total_kb + rss))
        entries+=("$rss $pid")
    done < <(get_descendants "$root")
    echo "$total_kb"
    printf '%s\n' "${entries[@]}" | sort -rn
}

run_loop() {
    local threshold_kb=$((THRESHOLD_GB * 1024 * 1024))
    local self=$$
    : > "$LOG_FILE"
    log "guard started root=$ROOT_PID threshold=${THRESHOLD_GB}G interval=${INTERVAL}s pid=$self"
    trap 'log "guard terminating"; rm -f "$PID_FILE"; exit 0' TERM INT HUP
    while true; do
        if ! kill -0 "$ROOT_PID" 2>/dev/null; then
            log "root pid $ROOT_PID gone; exiting"
            rm -f "$PID_FILE"
            exit 0
        fi
        local data total_kb
        data=$(scan_once "$ROOT_PID" "$self")
        total_kb=$(echo "$data" | head -n1)
        local entries
        entries=$(echo "$data" | tail -n +2)
        if [[ -n "$total_kb" && "$total_kb" -gt "$threshold_kb" ]]; then
            local total_gb=$((total_kb / 1024 / 1024))
            log "THRESHOLD EXCEEDED total=${total_gb}G > ${THRESHOLD_GB}G; killing descendants"
            while IFS=' ' read -r rss pid; do
                [[ -z "$pid" ]] && continue
                log "KILL pid=$pid comm=$(comm_of "$pid") rss_kb=$rss"
                kill -9 "$pid" 2>/dev/null || true
            done <<< "$entries"
            log "kill pass complete"
        fi
        sleep "$INTERVAL"
    done
}

cmd_start() {
    if [[ -f "$PID_FILE" ]]; then
        local old
        old=$(cat "$PID_FILE" 2>/dev/null || echo "")
        if [[ -n "$old" ]] && kill -0 "$old" 2>/dev/null; then
            echo "memory-guard already running (pid=$old, tag=$TAG)" >&2
            exit 1
        fi
        rm -f "$PID_FILE"
    fi
    if [[ -z "$ROOT_PID" ]]; then
        ROOT_PID=$(detect_root)
    fi
    if ! kill -0 "$ROOT_PID" 2>/dev/null; then
        echo "root pid $ROOT_PID not alive" >&2
        exit 2
    fi
    export MG_DAEMON=1 MG_THRESHOLD=$THRESHOLD_GB MG_INTERVAL=$INTERVAL MG_ROOT=$ROOT_PID
    export MEMORY_GUARD_TAG="$TAG"
    setsid nohup bash "$0" __daemon__ >/dev/null 2>&1 < /dev/null &
    local child=$!
    disown "$child" 2>/dev/null || true
    echo "$child" > "$PID_FILE"
    sleep 0.3
    if ! kill -0 "$child" 2>/dev/null; then
        echo "memory-guard failed to start; see $LOG_FILE" >&2
        rm -f "$PID_FILE"
        exit 3
    fi
    echo "memory-guard started pid=$child root=$ROOT_PID threshold=${THRESHOLD_GB}G interval=${INTERVAL}s tag=$TAG"
    echo "log: $LOG_FILE"
}

cmd_stop() {
    if [[ ! -f "$PID_FILE" ]]; then
        echo "memory-guard not running (tag=$TAG)"
        return 0
    fi
    local pid
    pid=$(cat "$PID_FILE" 2>/dev/null || echo "")
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
        sleep 0.2
        kill -9 "$pid" 2>/dev/null || true
        echo "stopped pid=$pid tag=$TAG"
    else
        echo "stale pid file removed"
    fi
    rm -f "$PID_FILE"
}

cmd_status() {
    if [[ -f "$PID_FILE" ]]; then
        local pid
        pid=$(cat "$PID_FILE" 2>/dev/null || echo "")
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            echo "running pid=$pid tag=$TAG"
            [[ -f "$LOG_FILE" ]] && { echo "--- log tail ---"; tail -n 10 "$LOG_FILE"; }
            return 0
        fi
    fi
    echo "not running (tag=$TAG)"
}

cmd_check() {
    if [[ -z "$ROOT_PID" ]]; then
        ROOT_PID=$(detect_root)
    fi
    local self=$$
    local data total_kb
    data=$(scan_once "$ROOT_PID" "$self")
    total_kb=$(echo "$data" | head -n1)
    local entries
    entries=$(echo "$data" | tail -n +2)
    local total_gb
    total_gb=$(awk -v k="$total_kb" 'BEGIN{printf "%.2f", k/1024/1024}')
    echo "root_pid=$ROOT_PID total_rss=${total_gb}G threshold=${THRESHOLD_GB}G"
    echo "--- top descendants (rss_kb pid comm) ---"
    if [[ -n "$entries" ]]; then
        while IFS=' ' read -r rss pid; do
            [[ -z "$pid" ]] && continue
            echo "$rss $pid $(comm_of "$pid")"
        done <<< "$entries" | head -n 15
    fi
}

# --- entry point -----------------------------------------------------

if [[ "${1:-}" == "__daemon__" ]]; then
    THRESHOLD_GB=${MG_THRESHOLD:-$THRESHOLD_GB}
    INTERVAL=${MG_INTERVAL:-$INTERVAL}
    ROOT_PID=${MG_ROOT:-}
    TAG=${MEMORY_GUARD_TAG:-$TAG}
    PID_FILE="/tmp/memory-guard-${USER}-${TAG}.pid"
    LOG_FILE="/tmp/memory-guard-${USER}-${TAG}.log"
    run_loop
    exit 0
fi

cmd="${1:-}"
shift || true
while [[ $# -gt 0 ]]; do
    case "$1" in
        --threshold) THRESHOLD_GB=$2; shift 2 ;;
        --interval)  INTERVAL=$2;     shift 2 ;;
        --root-pid)  ROOT_PID=$2;     shift 2 ;;
        --tag)       TAG=$2;          shift 2
                     PID_FILE="/tmp/memory-guard-${USER}-${TAG}.pid"
                     LOG_FILE="/tmp/memory-guard-${USER}-${TAG}.log" ;;
        -h|--help)   usage; exit 0 ;;
        *) echo "unknown arg: $1" >&2; usage; exit 1 ;;
    esac
done

case "$cmd" in
    start)  cmd_start ;;
    stop)   cmd_stop ;;
    status) cmd_status ;;
    check)  cmd_check ;;
    ""|-h|--help) usage ;;
    *) echo "unknown command: $cmd" >&2; usage; exit 1 ;;
esac
