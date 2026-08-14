#!/usr/bin/env bash
# pg_dump the running `postgres` compose service to a timestamped, gzipped file.
#
# Cron (daily at 3am, keep last 14 days):
#   0 3 * * * cd /path/to/fit-link && ./scripts/backup.sh >> /var/log/fitlink-backup.log 2>&1
#   5 3 * * * find /path/to/fit-link/backups -name '*.sql.gz' -mtime +14 -delete
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

: "${POSTGRES_USER:?POSTGRES_USER not set (check .env)}"
: "${POSTGRES_DB:?POSTGRES_DB not set (check .env)}"

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
OUT_FILE="${BACKUP_DIR}/fitlink-${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
  | gzip > "$OUT_FILE"

echo "Backup written to $OUT_FILE"
