# Backup & Recovery Guide

**Date:** 2026-02-10 11:25 UTC
**Phase:** Testing Foundation - Phase 5

---

## Quick Start

### Manual Database Backup

```bash
cd /home/jr/.openclaw/workspace/projects/gaastats-app
./scripts/backup-database.sh
```

### Manual Database Restore

```bash
cd /home/jr/.openclaw/workspace/projects/gaastats-app
./scripts/restore-database.sh backups/database/gaastats_20260210_020000.sql.gz
```

### Check Backup Status

```bash
# List all backups
ls -lh /home/jr/.openclaw/workspace/projects/gaastats-app/backups/database/

# Verify backup integrity
gzip -t backups/database/gaastats_*.sql.gz
```

---

## Backup Schedule

### Automated Backups (Cron)

```bash
# Edit crontab
crontab -e

# Add these lines:

# Database backup - Daily at 2 AM
0 2 * * * /home/jr/.openclaw/workspace/projects/gaastats-app/scripts/backup-database.sh >> /var/log/gaastats-backup.log 2>&1

# Database cleanup - Weekly (Sundays at 3 AM)
0 3 * * 0 find /home/jr/.openclaw/workspace/projects/gaastats-app/backups/database -name "gaastats_*.sql.gz" -mtime +7 -delete
```

### Backup Retention

- **Database backups:** Keep 7 days (daily)
- **Git repositories:** All commits retained (infinite)
- **Project files:** Weekly backup, 30-day retention

---

## Disaster Recovery Procedures

### Scenario 1: Database Corruption

**Symptoms:** Application errors, data inconsistencies

**Steps:**

1. **Stop the application**
   ```bash
   cd /home/jr/.openclaw/workspace/projects/gaastats-app/deployment
   docker-compose down
   ```

2. **Identify corruption**
   ```bash
   # Check database logs
   docker logs gaastats-postgres --tail 100
   ```

3. **List available backups**
   ```bash
   ls -lt /home/jr/.openclaw/workspace/projects/gaastats-app/backups/database/ | head -5
   ```

4. **Restore from latest good backup**
   ```bash
   cd /home/jr/.openclaw/workspace/projects/gaastats-app
   ./scripts/restore-database.sh backups/database/gaastats_<TIMESTAMP>.sql.gz
   ```

5. **Verify restoration**
   ```bash
   # Connect to database and check critical tables
   python manage.py shell
   >>> from gaastats.models import Club, Match, Player
   >>> Club.objects.count()
   >>> Match.objects.count()
   >>> Player.objects.count()
   ```

6. **Restart application**
   ```bash
   cd deployment
   docker-compose up -d
   ```

7. **Test critical functionality**
   - Login works
   - Can view matches
   - Can update player data

---

### Scenario 2: Server Crash (File System OK)

**Symptoms:** Server won't boot, Docker containers down

**Steps:**

1. **Start PostgreSQL manually**
   ```bash
   docker start gaastats-postgres
   docker start gaastats-redis
   ```

2. **Start application**
   ```bash
   cd /home/jr/.openclaw/workspace/projects/gaastats-app/deployment
   docker-compose up -d
   ```

3. **Check container status**
   ```bash
   docker ps
   ```

4. **Verify application health**
   ```bash
   curl http://localhost:8000/api/health/
   ```

---

### Scenario 3: Complete System Loss

**Symptoms:** Server lost, needs full rebuild

**Steps:**

#### Phase 1: Provision New Server

1. **Install dependencies**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER

   # Install Docker Compose
   sudo apt install docker-compose

   # Install PostgreSQL client
   sudo apt install postgresql-client

   # Install AWS CLI (for S3 backups)
   pip install awscli
   ```

2. **Configure environment**
   ```bash
   # Clone repository
   git clone https://github.com/johnrochie/project-darth.git
   cd project-darth
   ```

#### Phase 2: Restore Configuration

1. **Restore environment variables**
   ```bash
   # From backup location
   cp backups/config/project-darth_env_production .env
   ```

2. **Set proper permissions**
   ```bash
   chmod 600 .env
   ```

#### Phase 3: Restore Database

1. **Download latest backup from S3**
   ```bash
   aws s3 ls s3://johnrochie-backups/gaastats-database/ --recursive | tail -5
   aws s3 cp s3://johnrochie-backups/gaastats-database/gaastats_<LATEST>.sql.gz .
   ```

2. **Start databases**
   ```bash
   cd deployment
   docker-compose up -d postgres redis
   # Wait for databases to start
   sleep 30
   ```

3. **Restore database**
   ```bash
   cd ..
   ./scripts/restore-database.sh <LATEST_BACKUP_FILE>
   ```

4. **Run migrations (if needed)**
   ```bash
   cd backend
   python manage.py migrate
   ```

#### Phase 4: Restore Application

1. **Start Docker containers**
   ```bash
   cd deployment
   docker-compose up -d
   ```

2. **Check logs**
   ```bash
   docker-compose logs -f
   ```

3. **Test application**
   ```bash
   # Health check
   curl http://localhost:8000/api/health/

   # Test authentication
   curl -X POST http://localhost:8000/api/auth/login/ \
     -d '{"username":"admin","password":"<password>"}'
   ```

#### Phase 5: Verify Data

1. **Check database integrity**
   ```python
   python manage.py shell

   >>> from gaastats.models import Club, Match, Player
   >>> print(f"Clubs: {Club.objects.count()}")
   >>> print(f"Matches: {Match.objects.count()}")
   >>> print(f"Players: {Player.objects.count()}")
   ```

2. **Test critical functionality**
   - Login works
   - Can view clubs
   - Can update matches
   - WebSocket connections work

---

### Scenario 4: Git Repository Loss

**Steps:**

1. **Clone from GitHub**
   ```bash
   git clone https://github.com/johnrochie/project-darth.git
   cd project-darth
   ```

2. **Check for uncommitted changes**
   - Uncommitted changes are **lost** - this is why we pre-commit check!
   - Always commit before major changes

3. **Verify branches**
   ```bash
   git branch -a
   ```

4. **Restore from backup Git remote (if configured)**
   ```bash
   git remote add backup git@github.com:johnrochie-backup/project-darth.git
   git fetch backup --all
   git checkout main
   ```

---

## Backup Locations

### Local Storage

| Backup Type | Location | Retention |
|-------------|----------|-----------|
| Database | `/home/jr/.openclaw/workspace/projects/gaastats-app/backups/database/` | 7 days |
| Configuration | `/home/jr/.openclaw/workspace/projects/gaastats-app/backups/config/` | 30 days |
| Logs | `/var/log/gaastats-backup.log` | 30 days |

### Cloud Backup (S3)

| Backup Type | S3 Path | Retention |
|-------------|---------|-----------|
| Database | `s3://johnrochie-backups/gaastats-database/` | 7 days |
| Project Files | `s3://johnrochie-backups/workspace/` | 30 days |

---

## Monitoring & Alerts

### Check Backup Health

```bash
# Check backup schedule running
tail -50 /var/log/gaastats-backup.log

# Verify latest backup exists
ls -lh /home/jr/.openclaw/workspace/projects/gaastats-app/backups/database/ | head -3

# Check S3 backups (if configured)
aws s3 ls s3://johnrochie-backups/gaastats-database/ | tail -5
```

### Alert Thresholds

- **Database backup age:** Max 26 hours (should be daily)
- **Backup file integrity:** gzip test should pass
- **Disk space:** Min 10GB free for new backups
- **S3 upload status:** Should complete successfully

---

## Testing Backups

### Monthly Recovery Test

1. **Select a random backup**
   ```bash
   cd /home/jr/.openclaw/workspace/projects/gaastats-app
   BACKUP=$(ls -t backups/database/gaastats_*.sql.gz | head -1)
   echo "Testing backup: $BACKUP"
   ```

2. **Verify backup integrity**
   ```bash
   gzip -t "$BACKUP"
   echo "✅ Backup integrity: OK"
   ```

3. **Restore to test database**
   ```bash
   # Create test database
   PGPASSWORD="$DB_PASSWORD" createdb -h localhost -U postgres test_gaastats_restore

   # Restore
   gunzip -c "$BACKUP" | PGPASSWORD="$DB_PASSWORD" psql -h localhost -U postgres -d test_gaastats_restore

   # Drop test database
   PGPASSWORD="$DB_PASSWORD" dropdb -h localhost -U postgres test_gaastats_restore
   ```

4. **Document results**
   - Date: $(date)
   - Backup file: $BACKUP
   - Restored successfully: ✅
   - Data verified: ✅

---

## Troubleshooting

### Backup Fails

**Check:**
1. Database connection: `psql -h localhost -U postgres -d gaastats`
2. Disk space: `df -h`
3. Database access: Check DB_USER and DB_PASSWORD env vars

### Restore Fails

**Check:**
1. Backup file exists and not corrupted: `gzip -t <backup_file>`
2. Database is reachable and has permissions
3. Schema version matches backup

### S3 Upload Fails

**Check:**
1. AWS credentials: `aws sts get-caller-identity`
2. Bucket exists: `aws s3 ls s3://johnrochie-backups/`
3. Permissions: Can write to bucket

---

**Last Updated:** 2026-02-10 11:25 UTC
