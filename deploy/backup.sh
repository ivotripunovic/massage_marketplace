#!/bin/bash
# Database and media backup script for Massage Marketplace.
# Schedule via cron:
#   0 2 * * * /opt/marketplace/deploy/backup.sh >> /var/log/marketplace/backup.log 2>&1

set -euo pipefail

# ---- Configuration ----
APP_DIR="/opt/marketplace"
BACKUP_DIR="/var/backups/marketplace"
DB_NAME="${DB_NAME:-massage_marketplace}"
DB_USER="${DB_USER:-marketplace}"
RETENTION_DAYS=30

DATE=$(date +%Y%m%d_%H%M%S)
DB_BACKUP_FILE="${BACKUP_DIR}/db_${DATE}.sql.gz"
MEDIA_BACKUP_FILE="${BACKUP_DIR}/media_${DATE}.tar.gz"

# ---- Create backup directory ----
mkdir -p "${BACKUP_DIR}"

# ---- Database backup ----
echo "[$(date)] Starting database backup..."
pg_dump -U "${DB_USER}" "${DB_NAME}" | gzip > "${DB_BACKUP_FILE}"
echo "[$(date)] Database backup saved: ${DB_BACKUP_FILE}"

# ---- Media files backup (weekly: only on Sundays) ----
if [ "$(date +%u)" -eq 7 ]; then
    echo "[$(date)] Starting media backup..."
    tar -czf "${MEDIA_BACKUP_FILE}" -C "${APP_DIR}" media/
    echo "[$(date)] Media backup saved: ${MEDIA_BACKUP_FILE}"
fi

# ---- Cleanup old backups ----
echo "[$(date)] Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "db_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
find "${BACKUP_DIR}" -name "media_*.tar.gz" -mtime +${RETENTION_DAYS} -delete

echo "[$(date)] Backup complete."
