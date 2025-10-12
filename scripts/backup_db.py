#!/usr/bin/env python
"""
Database backup script.

Creates a timestamped backup copy of the database before migration.

Usage:
    python scripts/backup_db.py [--db-path data/messages.db] [--backup-dir backups]
"""

import argparse
import logging
import shutil
import sys
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_backup(db_path: str, backup_dir: str = 'backups') -> bool:
    """
    Create a backup copy of the database.

    Args:
        db_path: Path to database file
        backup_dir: Directory to store backups

    Returns:
        True if backup was successful, False otherwise
    """
    db_file = Path(db_path)

    if not db_file.exists():
        logger.error(f"Database file not found: {db_path}")
        return False

    # Create backup directory if it doesn't exist
    backup_path = Path(backup_dir)
    backup_path.mkdir(exist_ok=True)

    # Generate timestamped backup filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"{db_file.stem}_backup_{timestamp}{db_file.suffix}"
    backup_file = backup_path / backup_filename

    logger.info(f"Creating backup: {db_path} -> {backup_file}")

    try:
        shutil.copy2(db_path, backup_file)

        # Verify backup
        if backup_file.exists():
            original_size = db_file.stat().st_size
            backup_size = backup_file.stat().st_size

            if original_size == backup_size:
                logger.info(f"✅ Backup created successfully!")
                logger.info(f"   Original: {original_size} bytes")
                logger.info(f"   Backup:   {backup_size} bytes")
                logger.info(f"   Location: {backup_file}")
                return True
            else:
                logger.error("❌ Backup size mismatch!")
                logger.error(f"   Original: {original_size} bytes")
                logger.error(f"   Backup:   {backup_size} bytes")
                return False
        else:
            logger.error("❌ Backup file was not created")
            return False

    except Exception as e:
        logger.error(f"❌ Error creating backup: {e}")
        return False


def list_backups(backup_dir: str = 'backups'):
    """List all existing backups."""
    backup_path = Path(backup_dir)

    if not backup_path.exists():
        logger.info(f"No backups directory found at: {backup_dir}")
        return

    backups = sorted(backup_path.glob('*_backup_*.db'), reverse=True)

    if not backups:
        logger.info(f"No backups found in: {backup_dir}")
        return

    logger.info(f"\nExisting backups in {backup_dir}:")
    logger.info("-" * 60)

    for backup in backups:
        size = backup.stat().st_size
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        logger.info(f"  {backup.name}")
        logger.info(f"    Size: {size:,} bytes")
        logger.info(f"    Date: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")


def main():
    """Main entry point for backup script."""
    parser = argparse.ArgumentParser(
        description='Create database backup before migration'
    )
    parser.add_argument(
        '--db-path',
        default='data/messages.db',
        help='Path to database file (default: data/messages.db)'
    )
    parser.add_argument(
        '--backup-dir',
        default='backups',
        help='Directory to store backups (default: backups)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List existing backups'
    )

    args = parser.parse_args()

    if args.list:
        list_backups(args.backup_dir)
        sys.exit(0)

    logger.info("=" * 60)
    logger.info("Database Backup")
    logger.info("=" * 60)

    success = create_backup(args.db_path, args.backup_dir)

    if success:
        logger.info("=" * 60)
        logger.info("Backup completed successfully!")
        logger.info("You can now proceed with migration.")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("=" * 60)
        logger.error("Backup failed!")
        logger.error("Do not proceed with migration.")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
