#!/bin/bash
# Daily sync script for walks tracker
# Add to crontab: 0 6 * * * /opt/walks-tracker/scripts/sync-cron.sh

set -e

API_URL="${API_URL:-http://localhost:8000}"
LOG_FILE="/var/log/walks-sync.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting daily sync..."

# Trigger sync
response=$(curl -s -X POST "${API_URL}/api/sync" -H "Content-Type: application/json")

if echo "$response" | grep -q "sync_id"; then
    sync_id=$(echo "$response" | grep -o '"sync_id":[0-9]*' | cut -d':' -f2)
    log "Sync triggered successfully (ID: $sync_id)"
else
    log "ERROR: Failed to trigger sync"
    log "Response: $response"
    exit 1
fi

# Wait for sync to complete (max 5 minutes)
max_wait=300
waited=0
interval=10

while [ $waited -lt $max_wait ]; do
    sleep $interval
    waited=$((waited + interval))

    status=$(curl -s "${API_URL}/api/sync/status")

    if echo "$status" | grep -q '"status":"success"'; then
        records=$(echo "$status" | grep -o '"records_fetched":[0-9]*' | cut -d':' -f2)
        log "Sync completed successfully! Records fetched: $records"
        exit 0
    elif echo "$status" | grep -q '"status":"failed"'; then
        error=$(echo "$status" | grep -o '"error_message":"[^"]*"' | cut -d'"' -f4)
        log "ERROR: Sync failed - $error"
        exit 1
    fi

    log "Waiting for sync to complete... ($waited/$max_wait seconds)"
done

log "ERROR: Sync timed out after $max_wait seconds"
exit 1
