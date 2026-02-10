#!/bin/bash

# GAA Stats App - PostgreSQL Backup Script
# Automatically backs up the prod database with retention policy

set -e

# Configuration
DB_NAME="${DB_NAME:-gaastats}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
BACKUP_DIR="${BACKUP_DIR:-/home/jr/.openclaw/workspace/projects/gaastats-app/backups/database}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
S3_BUCKET="${S3_BUCKET:-}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/gaastats_${TIMESTAMP}.sql.gz"

echo "=========================================="
echo "GAA Stats Database Backup"
echo "=========================================="
echo "Timestamp: $TIMESTAMP"
echo "Database: $DB_NAME"
echo "Backup file: $BACKUP_FILE"
echo "=========================================="

# Backup database with compression
PGPASSWORD="${DB_PASSWORD}" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-acl \
    --verbose \
    | gzip > "$BACKUP_FILE"

# Check backup was successful
if [ -f "$BACKUP_FILE" ]; then
    size=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ Backup successful: $size"
else
    echo "❌ Backup failed!"
    exit 1
fi

# Upload to S3 (if AWS CLI configured)
if command -v aws &> /dev/null && [ -n "$S3_BUCKET" ]; then
    echo "Uploading to S3..."
    aws s3 cp "$BACKUP_FILE" "${S3_BUCKET}/gaastats_${TIMESTAMP}.sql.gz"
    echo "✅ S3 upload successful"
fi

# Cleanup old backups (retain N days)
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "gaastats_*.sql.gz" -mtime +$RETENTION_DAYS -delete
echo "✅ Cleanup complete"

echo "=========================================="
echo "Backup completed successfully!"
echo "=========================================="
