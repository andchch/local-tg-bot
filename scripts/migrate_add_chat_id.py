#!/usr/bin/env python
import argparse
import logging
import sqlite3
import sys
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def check_index_exists(cursor: sqlite3.Cursor, index_name: str) -> bool:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,))
    return cursor.fetchone() is not None


def migrate_database(db_path: str) -> bool:
    db_file = Path(db_path)

    if not db_file.exists():
        logger.error(f"Database file not found: {db_path}")
        return False

    logger.info(f"Starting migration for database: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if check_column_exists(cursor, 'messages', 'chat_id'):
            logger.info("✓ Column 'chat_id' already exists - migration not needed")
            conn.close()
            return True

        logger.info("Adding column 'chat_id' to messages table...")

        cursor.execute("""
            ALTER TABLE messages
            ADD COLUMN chat_id INTEGER NOT NULL DEFAULT 0
        """)
        logger.info("✓ Column 'chat_id' added successfully")

        if not check_index_exists(cursor, 'ix_messages_chat_id'):
            logger.info("Creating index on 'chat_id'...")
            cursor.execute("""
                CREATE INDEX ix_messages_chat_id ON messages (chat_id)
            """)
            logger.info("✓ Index 'ix_messages_chat_id' created")
        else:
            logger.info("✓ Index 'ix_messages_chat_id' already exists")

        if not check_index_exists(cursor, 'idx_chat_timestamp'):
            logger.info("Creating composite index on (chat_id, timestamp)...")
            cursor.execute("""
                CREATE INDEX idx_chat_timestamp ON messages (chat_id, timestamp)
            """)
            logger.info("✓ Index 'idx_chat_timestamp' created")
        else:
            logger.info("✓ Index 'idx_chat_timestamp' already exists")

        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM messages WHERE chat_id = 0")
        old_messages_count = cursor.fetchone()[0]

        if old_messages_count > 0:
            logger.warning(f"⚠ {old_messages_count} existing messages have chat_id=0 (unknown)")
            logger.warning("  These messages won't appear in per-chat queries")
            logger.warning("  You can manually update them if needed")

        conn.close()
        logger.info("✅ Migration completed successfully!")
        return True

    except sqlite3.Error as e:
        logger.error(f"❌ Database error during migration: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during migration: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Migrate database to add chat_id column'
    )
    parser.add_argument(
        '--db-path',
        default='data/messages.db',
        help='Path to database file (default: data/messages.db)'
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Database Migration: Add chat_id column")
    logger.info("=" * 60)

    success = migrate_database(args.db_path)

    if success:
        logger.info("=" * 60)
        logger.info("Migration completed successfully!")
        logger.info("You can now start the bot normally.")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("=" * 60)
        logger.error("Migration failed!")
        logger.error("Please check the error messages above.")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
