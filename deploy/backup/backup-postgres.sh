#!/usr/bin/env sh
# Daily PostgreSQL backup — schedule via cron or k8s CronJob.
# Example: 0 2 * * * /opt/erp/deploy/backup/backup-postgres.sh
set -eu

BACKUP_DIR="${BACKUP_DIR:-/var/backups/erp}"
RETAIN_DAYS="${RETAIN_DAYS:-14}"
STAMP=$(date +%Y%m%d_%H%M%S)
FILE="${BACKUP_DIR}/erp_db_${STAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U "${POSTGRES_USER:-erp}" "${POSTGRES_DB:-erp_db}" | gzip > "${FILE}"

find "${BACKUP_DIR}" -name 'erp_db_*.sql.gz' -mtime +"${RETAIN_DAYS}" -delete

echo "Backup written: ${FILE}"
