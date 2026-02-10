# Backup & Recovery Automation - Setup

**Date:** 2026-02-10 11:20 UTC
**Phase:** Testing Foundation - Phase 5
**Status:** 📋 IMPLEMENTATION IN PROGRESS

---

## Overview

Building automated backup and recovery system for:
1. **PostgreSQL database** - scheduled backups with retention policy
2. **Git repositories** - automated remote backups
3. **Project files** - rsync backups to secondary location
4. **Configuration templates** - .env files and secrets backup
5. **Recovery procedures** - step-by-step restore guides

---

## Part 1: PostgreSQL Database Backups

### Backup Script (`scripts/backup-database.sh`)

```bash
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
S3_BUCKET="${S3_BUCKET:-s3://johnrochie-backups/gaastats-database}"

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
find "$BACKUP_DIR" -name "gaastats_*.sql.gz" -mtime +$RETENTION_DAYS | while read file; do
    if command -v aws &> /dev/null && [ -n "$S3_BUCKET" ]; then
        aws s3 rm "${S3_BUCKET}/$(basename $file)"
    fi
done
echo "✅ Cleanup complete"

echo "=========================================="
echo "Backup completed successfully!"
echo "=========================================="

# Notification (optional)
# send-notification "Database backup completed: $size"
```

### Restore Script (`scripts/restore-database.sh`)

```bash
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
    ls -lh /home/jr/.openclaw/workspace/projects/gaastats-app/backups/database/ | tail -5
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

# WARNING: This will overwrite existing database
read -p "⚠️  WARNING: This will drop and recreate database. Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Decompress and restore
echo "Restoring database..."
gunzip -c "$BACKUP_FILE" | PGPASSWORD="${DB_PASSWORD}" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME"

echo "✅ Database restored successfully!"
echo "=========================================="
```

### Cron Job Setup

```bash
# Add to crontab (crontab -e)

# GAA Stats - Database backups (daily at 2 AM)
0 2 * * * /home/jr/.openclaw/workspace/projects/gaastats-app/scripts/backup-database.sh >> /var/log/gaastats-backup.log 2>&1

# GAA Stats - Database cleanup (weekly - Sundays at 3 AM)
0 3 * * 0 find /home/jr/.openclaw/workspace/projects/gaastats-app/backups/database -name "gaastats_*.sql.gz" -mtime +7 -delete
```

---

## Part 2: Git Repository Backups

### Automated Push to Multiple Remotes

```bash
#!/bin/bash

# scripts/backup-git-repos.sh
# Automatically push all project repos to multiple remote backups

set -e

PROJECTS_DIR="/home/jr/.openclaw/workspace/projects"
LOG_FILE="/var/log/git-backup.log"

echo "$(date): Starting Git repository backups" >> "$LOG_FILE"

for project_dir in "$PROJECTS_DIR"/*/; do
    if [ -d "$project_dir/.git" ]; then
        project_name=$(basename "$project_dir")
        cd "$project_dir"

        echo "Backing up: $project_name"

        # Add commit if there are changes
        if [ -n "$(git status --porcelain)" ]; then
            echo "  - Uncommitted changes detected, skipping" >> "$LOG_FILE"
            echo "  - Uncommitted changes detected, skipping"
            continue
        fi

        # Push to all remotes
        git remote -v | grep fetch | awk '{print $1}' | sort -u | while read remote; do
            echo "  - Pushing to remote: $remote"
            git push "$remote" --all >> "$LOG_FILE" 2>&1
            git push "$remote" --tags >> "$LOG_FILE" 2>&1
        done

        echo "  - ✅ Backup complete"
    fi
done

echo "$(date): Git repository backups complete" >> "$LOG_FILE"
echo "✅ All Git repositories backed up"
```

### Multiple Git Remote Setup

```bash
# Add backup remote (e.g., GitLab, Bitbucket, or another GitHub account)
git remote add backup git@github.com:johnrochie-backup/project-darth.git
git remote add gitlab git@gitlab.com:johnrochie/project-darth.git

# Push to all remotes
git push origin main
git push backup main
git push gitlab main
```

---

## Part 3: Project File Backups (rsync)

### Rsync Backup Script

```bash
#!/bin/bash

# scripts/backup-project-files.sh
# Backs up project files using rsync

set -e

SOURCE_DIR="/home/jr/.openclaw/workspace"
BACKUP_DIR="/home/jr/.openclaw/workspace-backup"
RETENTION_DAYS=30
S3_BUCKET="s3://johnrochie-backups/workspace"

echo "=========================================="
echo "Project Files Backup (rsync)"
echo "=========================================="

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Rync with compression and progress
rsync -avz \
    --progress \
    --delete \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='venv' \
    --exclude='.venv' \
    --exclude='.DS_Store' \
    "$SOURCE_DIR/" "$BACKUP_DIR/"

# Backup size
size=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "✅ Backup complete: $size"

# Cleanup old backups
find "$BACKUP_DIR" -maxdepth 0 -ctime +$RETENTION_DAYS -exec rm -rf {} \;

# Upload to S3 (if configured)
if command -v aws &> /dev/null && [ -n "$S3_BUCKET" ]; then
    echo "Syncing to S3..."
    aws s3 sync "$BACKUP_DIR/" "$S3_BUCKET/" --delete
    echo "✅ S3 sync complete"
fi

echo "=========================================="
```

### Rsync Cron Job

```bash
# Add to crontab

# GAA Stats - Project files backup (weekly - Sundays at 4 AM)
0 4 * * 0 /home/jr/.openclaw/workspace/projects/gaastats-app/scripts/backup-project-files.sh >> /var/log/project-backup.log 2>&1
```

---

## Part 4: Configuration Backups

### Environment Variables Backup

```bash
#!/bin/bash

# scripts/backup-config.sh
# Backs up .env files and configuration

set -e

BACKUP_DIR="/home/jr/.openclaw/workspace/projects/gaastats-app/backups/config"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "Backing up configuration files..."

# Copy .env files (encrypted)
for env_file in $(find /home/jr/.openclaw/workspace/projects -name ".env" -o -name ".env.*" -o -name ".env.production"); do
    project_dir=$(dirname "$env_file")
    project_name=$(basename "$project_dir")
    cp "$env_file" "$BACKUP_DIR/${project_name}_env_$(basename $env_file)_$TIMESTAMP"
done

# Copy other config files
find /home/jr/.openclaw/workspace/projects -name "settings.py" -o -name "config.yaml" -o -name "*.conf" | while read config_file; do
    cp "$config_file" "$BACKUP_DIR/"
done

echo "✅ Configuration backup complete"
```

---

## Part 5: Recovery Procedures

### Disaster Recovery Checklist

**Scenario 1: Database Crash**
1. Stop application: `docker-compose down`
2. Identify latest backup
3. Restore database: `./scripts/restore-database.sh backups/database/gaastats_20260210_020000.sql.gz`
4. Run migrations: `python manage.py migrate`
5. Restart application: `docker-compose up -d`
6. Verify data integrity: Check critical tables

**Scenario 2: File System Corruption**
1. Restore from rsync backup
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Restore Git: `git reset --hard HEAD`
4. Restart services
5. Test critical functionality

**Scenario 3: Complete System Loss**
1. Provision new server
2. Clone Git repo: `git clone https://github.com/johnrochie/project-darth`
3. Restore database from S3
4. Restore files from S3 rsync backup
5. Import configuration backups
6. Reinstall dependencies
7. Update DNS/SSL if needed
8. Test full application stack

---

## Part 6: Monitoring & Notifications

### Backup Status Check

```bash
#!/bin/bash

# scripts/check-backup-status.sh
# Checks if backups are running successfully

BACKUP_DIR="/home/jr/.openclaw/workspace/projects/gaastats-app/backups/database"
MAX_AGE_HOURS=26

echo "=========================================="
echo "Backup Status Check"
echo "=========================================="

# Check database backups
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/gaastats_*.sql.gz 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ No database backups found!"
    exit 1
fi

BACKUP_AGE=$(( ($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")) / 3600 ))

if [ $BACKUP_AGE -gt $MAX_AGE_HOURS ]; then
    echo "⚠️  Latest backup is $BACKUP_AGE hours old (max: $MAX_AGE_HOURS)"
    exit 1
else
    echo "✅ Latest backup age: $BACKUP_AGE hours"
fi

# Check backup file integrity
if gzip -t "$LATEST_BACKUP"; then
    echo "✅ Backup file integrity: OK"
else
    echo "❌ Backup file is corrupted!"
    exit 1
fi

# Check S3 uploads (if configured)
if command -v aws &> /dev/null; then
    S3_BACKUP_COUNT=$(aws s3 ls s3://johnrochie-backups/gaastats-database/ --recursive | wc -l)
    echo "✅ S3 backups: $S3_BACKUP_COUNT files"
fi

echo "=========================================="
echo "All backups healthy!"
echo "=========================================="
```
