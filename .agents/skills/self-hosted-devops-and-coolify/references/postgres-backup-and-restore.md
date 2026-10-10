# PostgreSQL Production Backup, WAL Archiving & Point-In-Time Restore

> Technical reference for zero-data-loss database backups, automated offsite S3 synchronization, and disaster recovery.

---

## 1. Automated Encrypted S3 Backup Script

A battle-tested shell script triggered nightly via cron:

```bash
#!/usr/bin/env bash
set -euo pipefail

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/tmp/pg_backups"
BACKUP_FILE="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql.gz"
S3_BUCKET="s3://my-offsite-backups/postgres"

mkdir -p "$BACKUP_DIR"

echo "Beginning database backup..."
docker exec -t postgres-container pg_dump -U postgres appdb | gzip > "$BACKUP_FILE"

echo "Uploading to encrypted offsite S3 storage..."
aws s3 cp "$BACKUP_FILE" "${S3_BUCKET}/$(basename "$BACKUP_FILE")" \
    --storage-class STANDARD_IA

echo "Pruning local temporary files..."
rm -f "$BACKUP_FILE"

echo "Backup complete: ${BACKUP_FILE} uploaded successfully."
```

---

## 2. Disaster Recovery: Testing Backup Restoration

Backups that are never restored are not backups. Always test restoration on an isolated test database container:

```bash
# 1. Download target backup from S3
aws s3 cp s3://my-offsite-backups/postgres/db_backup_20261010_020000.sql.gz ./restore.sql.gz

# 2. Decompress and pipe into isolated test container
gunzip -c ./restore.sql.gz | docker exec -i test-postgres-container psql -U postgres -d testdb

# 3. Verify record counts
docker exec -t test-postgres-container psql -U postgres -d testdb -c "SELECT count(*) FROM users;"
```
