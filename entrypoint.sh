#!/bin/bash

set -euo pipefail

readonly LOG_LEVEL="${LOG_LEVEL:-info}"
readonly HOST="${HOST:-0.0.0.0}"
readonly PORT="${PORT:-8000}"

readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

error_exit() {
    log_error "$1"
    exit "${2:-1}"
}

wait_for_service() {
    local service="$1"
    local host="$2"
    local port="$3"
    local max_attempts="${4:-30}"
    local attempt=1

    log_info "Waiting for $service at $host:$port..."

    while [[ $attempt -le $max_attempts ]]; do
        if timeout 2 bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
            log_info "$service is ready after $attempt attempts"
            return 0
        fi
        sleep 2
        ((attempt++))
    done

    error_exit "$service failed after $max_attempts attempts"
}

wait_for_dependencies() {
    log_info "Waiting for dependencies..."

    if [[ "${DATABASE_URL:-}" =~ postgresql://.*@([^:/]+):?([0-9]+)? ]]; then
        local db_host="${BASH_REMATCH[1]}"
        local db_port="${BASH_REMATCH[2]:-5432}"
        wait_for_service "PostgreSQL" "$db_host" "$db_port"
    fi

    if [[ "${REDIS_URL:-}" =~ redis://([^:/]+):?([0-9]+)? ]]; then
        local redis_host="${BASH_REMATCH[1]}"
        local redis_port="${BASH_REMATCH[2]:-6379}"
        wait_for_service "Redis" "$redis_host" "$redis_port"
    fi

    log_info "All dependencies ready"
}

start_api() {
    log_info "Starting Highlight Detector API..."
    exec uvicorn app.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --log-level "$LOG_LEVEL"
}

start_worker() {
    log_info "Starting Celery worker..."
    exec celery -A app.core.celery_app worker --loglevel=info
}

main() {
    local mode="${1:-api}"

    log_info "=== Highlight Detector Entrypoint ==="

    wait_for_dependencies

    case "$mode" in
        api)
            start_api
            ;;
        worker)
            start_worker
            ;;
        *)
            error_exit "Unknown mode: $mode. Use 'api' or 'worker'"
            ;;
    esac
}

main "$@"