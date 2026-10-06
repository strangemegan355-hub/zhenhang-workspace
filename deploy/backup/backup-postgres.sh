#!/usr/bin/env sh
# Daily PostgreSQL backup — schedule via cron or k8s CronJob.
# Example: 0 2 * * * /opt/erp/deploy/backup/backup-postgres.sh
set -euo pipefail

ROOT_DIR="$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-${ROOT_DIR}/docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-${ROOT_DIR}/backend/.env.prod}"
BACKUP_DIR="${BACKUP_DIR:-${ROOT_DIR}/volumes/backups/postgres}"
RETAIN_DAYS="${RETAIN_DAYS:-14}"
STAMP=$(date +%Y%m%d_%H%M%S)
FILE="${BACKUP_DIR}/erp_db_${STAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

# Write to a temporary name and move it into place only once the dump has succeeded. Redirecting straight
# into ${FILE} leaves a truncated file when pg_dump fails - one that keeps a backup's name and passes
# `gzip -t`, because gzip closes a valid empty stream - so an unattended cron would fill this directory
# with files that restore to nothing. The trap also cleans up an interrupted run.
TMP="${FILE}.part"
trap 'rm -f "${TMP}"' EXIT INT TERM

docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T postgres \
  pg_dump -U "${POSTGRES_USER:-erp}" "${POSTGRES_DB:-erp_db}" | gzip -9 > "${TMP}"

mv "${TMP}" "${FILE}"

find "${BACKUP_DIR}" -name 'erp_db_*.sql.gz' -mtime +"${RETAIN_DAYS}" -delete

echo "Backup written: ${FILE} (retention ${RETAIN_DAYS} days)"
