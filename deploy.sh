#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DEPLOY_HOST="${DEPLOY_HOST:-michael@100.115.127.119}"
DEPLOY_PATH="${DEPLOY_PATH:-~/walks-tracker}"
REMOTE_FRONTEND_URL="${REMOTE_FRONTEND_URL:-http://localhost:3080/}"
REMOTE_API_HEALTH_URL="${REMOTE_API_HEALTH_URL:-http://localhost:3080/api/health}"
DOCKER_PRUNE_UNTIL="${DOCKER_PRUNE_UNTIL:-24h}"
NO_CACHE=0
SSH_OPTS=(
  "-o" "BatchMode=yes"
  "-o" "ConnectTimeout=10"
  "-o" "ServerAliveInterval=5"
  "-o" "ServerAliveCountMax=3"
  "-o" "StrictHostKeyChecking=yes"
  "-o" "UserKnownHostsFile=${SCRIPT_DIR}/deploy_known_hosts"
)

RSYNC_EXCLUDES=(
  "--exclude=.git"
  "--exclude=.claude"
  "--exclude=node_modules"
  "--exclude=__pycache__"
  "--exclude=.env"
  "--exclude=venv"
  "--exclude=.venv"
  "--exclude=frontend/dist"
  "--exclude=.DS_Store"
)

log() {
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

usage() {
  cat <<'EOF'
Usage: ./deploy.sh [--no-cache] [--host <user@host>] [--path <remote-path>]

Options:
  --no-cache         Rebuild Docker images without using cache
  --host <user@host> Override the SSH host target
  --path <path>      Override the remote deploy path
  --help             Show this help text
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-cache)
      NO_CACHE=1
      shift
      ;;
    --host)
      DEPLOY_HOST="$2"
      shift 2
      ;;
    --path)
      DEPLOY_PATH="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

remote_sync_path() {
  case "$DEPLOY_PATH" in
    /*|~*)
      printf '%s\n' "$DEPLOY_PATH"
      ;;
    *)
      printf '~/%s\n' "$DEPLOY_PATH"
      ;;
  esac
}

wait_for_remote() {
  local description="$1"
  shift
  log "$description"
  ssh "${SSH_OPTS[@]}" "$DEPLOY_HOST" bash -s -- "$@" <<'REMOTE'
set -euo pipefail

raw_deploy_path="$1"
frontend_url="$2"
api_health_url="$3"
prune_until="$4"
no_cache="$5"

expand_path() {
  case "$1" in
    "~")
      printf '%s\n' "$HOME"
      ;;
    "~/"*)
      printf '%s/%s\n' "$HOME" "${1#~/}"
      ;;
    *)
      printf '%s\n' "$1"
      ;;
  esac
}

deploy_path="$(expand_path "$raw_deploy_path")"

wait_for_state() {
  local container="$1"
  local expected="$2"
  local timeout_seconds="$3"
  local started_at
  started_at="$(date +%s)"

  while true; do
    local current_status
    current_status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container" 2>/dev/null || true)"

    if [[ "$current_status" == "$expected" ]]; then
      echo "$container is $expected"
      return 0
    fi

    if (( "$(date +%s)" - started_at >= timeout_seconds )); then
      echo "Timed out waiting for $container to become $expected. Current status: ${current_status:-missing}" >&2
      docker logs --tail 50 "$container" || true
      exit 1
    fi

    sleep 2
  done
}

http_ok() {
  local url="$1"
  if command -v curl >/dev/null 2>&1; then
    curl -fsS "$url" >/dev/null
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- "$url" >/dev/null
  else
    echo "Remote host needs curl or wget for HTTP health checks" >&2
    exit 1
  fi
}

wait_for_http() {
  local url="$1"
  local timeout_seconds="$2"
  local started_at
  started_at="$(date +%s)"

  while true; do
    if http_ok "$url"; then
      echo "HTTP health check passed: $url"
      return 0
    fi

    if (( "$(date +%s)" - started_at >= timeout_seconds )); then
      echo "Timed out waiting for HTTP health check: $url" >&2
      exit 1
    fi

    sleep 2
  done
}

cd "$deploy_path/docker"

if [[ "$no_cache" == "1" ]]; then
  docker compose build --no-cache
  docker compose up -d --remove-orphans
else
  docker compose up -d --build --remove-orphans
fi

wait_for_state "walks-mysql" "healthy" 120
wait_for_state "walks-api" "healthy" 120
wait_for_state "walks-frontend" "healthy" 120
wait_for_http "$frontend_url" 60
wait_for_http "$api_health_url" 60

docker builder prune -af --filter "until=${prune_until}" >/dev/null || true
docker image prune -af --filter "until=${prune_until}" >/dev/null || true

docker compose ps
REMOTE
}

log "Ensuring remote path exists on ${DEPLOY_HOST}:${DEPLOY_PATH}"
ssh "${SSH_OPTS[@]}" "$DEPLOY_HOST" bash -s -- "$DEPLOY_PATH" <<'REMOTE'
set -euo pipefail

raw_deploy_path="$1"
case "$raw_deploy_path" in
  "~")
    deploy_path="$HOME"
    ;;
  "~/"*)
    deploy_path="$HOME/${raw_deploy_path#~/}"
    ;;
  *)
    deploy_path="$raw_deploy_path"
    ;;
esac

mkdir -p "$deploy_path"
REMOTE

log "Syncing project to ${DEPLOY_HOST}:${DEPLOY_PATH}"
rsync -avz --delete -e "ssh ${SSH_OPTS[*]}" "${RSYNC_EXCLUDES[@]}" "${SCRIPT_DIR}/" "${DEPLOY_HOST}:$(remote_sync_path)/"

wait_for_remote \
  "Deploying Docker stack and running health checks" \
  "$DEPLOY_PATH" \
  "$REMOTE_FRONTEND_URL" \
  "$REMOTE_API_HEALTH_URL" \
  "$DOCKER_PRUNE_UNTIL" \
  "$NO_CACHE"

log "Deploy complete"
