# Migration Scripts

This directory contains database migration and maintenance scripts for TopBot.

## Scripts

### `backup_db.py`

Creates timestamped backup copies of the database.

**Usage:**
```bash
# Create backup with default settings
python scripts/backup_db.py

# Specify custom database path
python scripts/backup_db.py --db-path path/to/database.db

# Specify custom backup directory
python scripts/backup_db.py --backup-dir my_backups

# List existing backups
python scripts/backup_db.py --list
```

**Output:**
- Backups are stored in `backups/` directory by default
- Filename format: `messages_backup_YYYYMMDD_HHMMSS.db`
- Script verifies backup integrity by comparing file sizes

### `migrate_add_chat_id.py`

Migrates database schema to add the `chat_id` column required for per-chat message filtering.

**Usage:**
```bash
# Run migration with default database
python scripts/migrate_add_chat_id.py

# Specify custom database path
python scripts/migrate_add_chat_id.py --db-path path/to/database.db
```

**What it does:**
1. Checks if `chat_id` column already exists (safe to run multiple times)
2. Adds `chat_id` column with DEFAULT 0 for existing messages
3. Creates index on `chat_id`
4. Creates composite index on `(chat_id, timestamp)`
5. Reports statistics about migrated messages

**Important:**
- Old messages will have `chat_id=0` and won't appear in per-chat queries
- Always backup before running migration
- Migration is idempotent (safe to run multiple times)

## Workflow for Database Updates

When upgrading TopBot to a version with schema changes:

```bash
# Step 1: Backup
python scripts/backup_db.py

# Step 2: Verify backup was created
python scripts/backup_db.py --list

# Step 3: Run migration
python scripts/migrate_add_chat_id.py

# Step 4: Start bot (will validate schema automatically)
python bot/main.py
```

## Troubleshooting

**Migration fails:**
- Check file permissions on database file
- Ensure database is not locked by another process
- Check disk space
- Review error messages for specific issues

**Bot won't start after migration:**
- Check `python scripts/migrate_add_chat_id.py` output for errors
- Verify all indexes were created successfully
- Try restoring from backup and re-running migration

**Restore from backup:**
```bash
# Stop the bot first
# Copy backup file over current database
cp backups/messages_backup_YYYYMMDD_HHMMSS.db data/messages.db
# Restart bot
```

## Development

When adding new migrations:

1. Create new script following naming convention: `migrate_<description>.py`
2. Include:
   - Argument parser for `--db-path`
   - Check if migration already applied
   - Detailed logging
   - Error handling
   - Verification step
3. Update CLAUDE.md with migration instructions
4. Test with existing database
5. Test idempotency (running twice should be safe)
