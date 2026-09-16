#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS="$ROOT/scripts"
RUN="$ROOT/.run"
LOGS="$RUN/logs"
DATA="$RUN/data"
RELAY_ENV="$RUN/relay.env"
cd "$ROOT"

mkdir -p "$RUN" "$LOGS" "$DATA"

SERVICES="$(grep '=' "$SCRIPTS/ports.env" || true)"

service_names() {
  printf "%s\n" "$SERVICES" | sed '/^$/d' | cut -d= -f1
}

service_port() {
  printf "%s\n" "$SERVICES" | sed '/^$/d' | awk -F= -v n="$1" '$1==n{print $2; exit}'
}

service_url() {
  local base
  base="http://localhost:$(service_port "$1")"
  case "$1" in
    webhook_server) printf "%s/api/houses\n" "$base" ;;
    listener) printf "%s/api/events\n" "$base" ;;
    *) printf "%s\n" "$base" ;;
  esac
}

export_ports() {
  export WEBHOOK_SERVER_PORT LISTENER_PORT ADMIN_UI_PORT
  WEBHOOK_SERVER_PORT="$(service_port webhook_server)"
  LISTENER_PORT="$(service_port listener)"
  ADMIN_UI_PORT="$(service_port admin_ui)"
}

load_relay() {
  [ -f "$RELAY_ENV" ] || fail "relay is not configured, run ./scripts/setup.sh first"
  set -a
  . "$RELAY_ENV"
  set +a
}

listener_connected() {
  curl -fsS "http://localhost:$(service_port listener)/health" 2>/dev/null | grep -q '"relay_connected": true'
}

wait_listener_connected() {
  local tries
  tries=60
  while [ "$tries" -gt 0 ]; do
    if listener_connected; then return 0; fi
    sleep 1
    tries=$((tries - 1))
  done
  return 1
}

port_pid() {
  lsof -ti "tcp:$1" -sTCP:LISTEN 2>/dev/null | head -1 || true
}

port_up() {
  [ -n "$(port_pid "$1")" ]
}

wait_port_up() {
  local tries
  tries="${2:-60}"
  while [ "$tries" -gt 0 ]; do
    if port_up "$1"; then return 0; fi
    sleep 1
    tries=$((tries - 1))
  done
  return 1
}

wait_port_down() {
  local tries
  tries="${2:-30}"
  while [ "$tries" -gt 0 ]; do
    if ! port_up "$1"; then return 0; fi
    sleep 1
    tries=$((tries - 1))
  done
  return 1
}

start_bg() {
  local name
  name="$1"
  shift
  if [ -f "$RUN/$name.pid" ] && kill -0 "$(cat "$RUN/$name.pid")" 2>/dev/null; then
    log "$name already running"
    return 0
  fi
  ( cd "$ROOT" && exec "$@" >"$LOGS/$name.log" 2>&1 ) &
  echo $! >"$RUN/$name.pid"
  log "$name started pid $!"
}

stop_bg() {
  local name pid port
  name="$1"
  if [ -f "$RUN/$name.pid" ]; then
    pid="$(cat "$RUN/$name.pid")"
    if kill -0 "$pid" 2>/dev/null; then
      kill -TERM "$pid" 2>/dev/null || true
    fi
    rm -f "$RUN/$name.pid"
  fi
  port="$(service_port "$name")"
  wait_port_down "$port" 10 || true
  pid="$(port_pid "$port")"
  if [ -n "$pid" ]; then kill -KILL "$pid" 2>/dev/null || true; fi
  log "$name stopped"
}

open_url() {
  if command -v open >/dev/null 2>&1; then
    open "$1"
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$1"
  else
    fail "no browser opener found, open $1 manually"
  fi
}

require() {
  command -v "$1" >/dev/null 2>&1 || fail "$1 is required but not installed"
}

log() {
  printf "%s\n" "$*"
}

fail() {
  printf "ERROR: %s\n" "$*" >&2
  exit 1
}
