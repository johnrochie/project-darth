#!/bin/bash

# GAA Stats App - PostgreSQL Restore Script
# Restores database from backup

set -e

# Configuration
DB_NAME="${DB_NAME:-gaastats}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo "Available backups:"
    ls -lh /home/jr/.openclaw/workspace/projects/gaastats-app/backups/database/ 2>/dev/null | tail -10 || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "=========================================="
echo "GAA Stats Database Restore"
echo "=========================================="
echo "Backup: $BACKUP_FILE"
echo "Database: $DB_NAME"
echo "=========================================="

# Decompress and restore
echo "Restoring database..."
gunzip -c "$BACKUP_FILE" | PGPASSWORD="${DB_PASSWORD}" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME"

echo "✅ Database restored successfully!"
echo "=========================================="
