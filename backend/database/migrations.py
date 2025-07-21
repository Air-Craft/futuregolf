"""
Database migration utilities for FutureGolf application.
This module provides utilities for managing database schema changes.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import json

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.config import engine, logger
from sqlalchemy import text, inspect
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


class Migration:
    """Represents a database migration."""
    
    def __init__(self, name: str, timestamp: str, up_sql: str, down_sql: str):
        self.name = name
        self.timestamp = timestamp
        self.up_sql = up_sql
        self.down_sql = down_sql
    
    @property
    def filename(self):
        return f"{self.timestamp}_{self.name}.json"
    
    def to_dict(self):
        return {
            "name": self.name,
            "timestamp": self.timestamp,
            "up_sql": self.up_sql,
            "down_sql": self.down_sql,
            "created_at": datetime.utcnow().isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            name=data["name"],
            timestamp=data["timestamp"],
            up_sql=data["up_sql"],
            down_sql=data["down_sql"]
        )


def ensure_migrations_table():
    """Create the migrations tracking table if it doesn't exist."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        id SERIAL PRIMARY KEY,
        migration_name VARCHAR(255) NOT NULL UNIQUE,
        applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        checksum VARCHAR(64)
    );
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()


def get_applied_migrations() -> List[str]:
    """Get list of applied migration names."""
    ensure_migrations_table()
    
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT migration_name FROM schema_migrations ORDER BY applied_at"
        ))
        return [row[0] for row in result.fetchall()]


def mark_migration_applied(migration_name: str):
    """Mark a migration as applied."""
    ensure_migrations_table()
    
    with engine.connect() as conn:
        conn.execute(text(
            "INSERT INTO schema_migrations (migration_name) VALUES (:name)"
        ), {"name": migration_name})
        conn.commit()


def mark_migration_unapplied(migration_name: str):
    """Mark a migration as unapplied (remove from applied migrations)."""
    ensure_migrations_table()
    
    with engine.connect() as conn:
        conn.execute(text(
            "DELETE FROM schema_migrations WHERE migration_name = :name"
        ), {"name": migration_name})
        conn.commit()


def create_migration(name: str, up_sql: str, down_sql: str) -> Migration:
    """Create a new migration file."""
    # Ensure migrations directory exists
    MIGRATIONS_DIR.mkdir(exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    # Create migration object
    migration = Migration(name, timestamp, up_sql, down_sql)
    
    # Save migration file
    migration_file = MIGRATIONS_DIR / migration.filename
    with open(migration_file, 'w') as f:
        json.dump(migration.to_dict(), f, indent=2)
    
    logger.info(f"Created migration: {migration.filename}")
    return migration


def load_migration(filename: str) -> Migration:
    """Load a migration from file."""
    migration_file = MIGRATIONS_DIR / filename
    
    if not migration_file.exists():
        raise FileNotFoundError(f"Migration file not found: {filename}")
    
    with open(migration_file, 'r') as f:
        data = json.load(f)
    
    return Migration.from_dict(data)


def get_pending_migrations() -> List[str]:
    """Get list of pending migration filenames."""
    if not MIGRATIONS_DIR.exists():
        return []
    
    applied = get_applied_migrations()
    all_migrations = []
    
    for file in MIGRATIONS_DIR.glob("*.json"):
        migration = load_migration(file.name)
        if migration.name not in applied:
            all_migrations.append(file.name)
    
    return sorted(all_migrations)


def apply_migration(migration: Migration) -> bool:
    """Apply a single migration."""
    logger.info(f"Applying migration: {migration.name}")
    
    try:
        with engine.connect() as conn:
            # Execute the up SQL
            for statement in migration.up_sql.split(';'):
                statement = statement.strip()
                if statement:
                    conn.execute(text(statement))
            
            conn.commit()
            
        # Mark as applied
        mark_migration_applied(migration.name)
        logger.info(f"Successfully applied migration: {migration.name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply migration {migration.name}: {e}")
        return False


def rollback_migration(migration: Migration) -> bool:
    """Rollback a single migration."""
    logger.info(f"Rolling back migration: {migration.name}")
    
    try:
        with engine.connect() as conn:
            # Execute the down SQL
            for statement in migration.down_sql.split(';'):
                statement = statement.strip()
                if statement:
                    conn.execute(text(statement))
            
            conn.commit()
            
        # Mark as unapplied
        mark_migration_unapplied(migration.name)
        logger.info(f"Successfully rolled back migration: {migration.name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to rollback migration {migration.name}: {e}")
        return False


def migrate_up():
    """Apply all pending migrations."""
    logger.info("Running database migrations...")
    
    pending = get_pending_migrations()
    
    if not pending:
        logger.info("No pending migrations.")
        return True
    
    logger.info(f"Found {len(pending)} pending migrations")
    
    for filename in pending:
        migration = load_migration(filename)
        if not apply_migration(migration):
            logger.error(f"Migration failed: {filename}")
            return False
    
    logger.info("All migrations applied successfully!")
    return True


def migrate_down(steps: int = 1):
    """Rollback the last N migrations."""
    logger.info(f"Rolling back {steps} migrations...")
    
    applied = get_applied_migrations()
    
    if not applied:
        logger.info("No migrations to rollback.")
        return True
    
    # Get the last N migrations to rollback
    to_rollback = applied[-steps:]
    
    for migration_name in reversed(to_rollback):
        # Find the migration file
        migration_file = None
        for file in MIGRATIONS_DIR.glob("*.json"):
            migration = load_migration(file.name)
            if migration.name == migration_name:
                migration_file = file.name
                break
        
        if not migration_file:
            logger.error(f"Migration file not found for: {migration_name}")
            return False
        
        migration = load_migration(migration_file)
        if not rollback_migration(migration):
            logger.error(f"Rollback failed: {migration_name}")
            return False
    
    logger.info(f"Successfully rolled back {steps} migrations!")
    return True


def migration_status():
    """Show migration status."""
    logger.info("Migration Status:")
    logger.info("================")
    
    applied = get_applied_migrations()
    pending = get_pending_migrations()
    
    logger.info(f"Applied migrations: {len(applied)}")
    for migration_name in applied:
        logger.info(f"  ✓ {migration_name}")
    
    logger.info(f"Pending migrations: {len(pending)}")
    for filename in pending:
        migration = load_migration(filename)
        logger.info(f"  ○ {migration.name}")


def create_initial_migration():
    """Create an initial migration for existing schema."""
    logger.info("Creating initial migration...")
    
    # Get current schema
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if not tables:
        logger.info("No tables found. Run database initialization first.")
        return False
    
    up_sql = "-- Initial schema migration (tables already exist)\nSELECT 1;"
    down_sql = "-- Drop all tables\n" + "\n".join([
        f"DROP TABLE IF EXISTS {table} CASCADE;" for table in tables
    ])
    
    create_migration("initial_schema", up_sql, down_sql)
    
    # Mark as applied since tables already exist
    mark_migration_applied("initial_schema")
    
    logger.info("Initial migration created and marked as applied.")
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FutureGolf Database Migrations")
    parser.add_argument("--up", action="store_true", help="Apply pending migrations")
    parser.add_argument("--down", type=int, default=1, help="Rollback N migrations")
    parser.add_argument("--status", action="store_true", help="Show migration status")
    parser.add_argument("--create", type=str, help="Create new migration")
    parser.add_argument("--initial", action="store_true", help="Create initial migration")
    
    args = parser.parse_args()
    
    if args.status:
        migration_status()
    elif args.up:
        if migrate_up():
            sys.exit(0)
        else:
            sys.exit(1)
    elif args.down:
        if migrate_down(args.down):
            sys.exit(0)
        else:
            sys.exit(1)
    elif args.create:
        print("Migration name:", args.create)
        print("Enter UP SQL (press Ctrl+D when done):")
        up_sql = sys.stdin.read()
        print("Enter DOWN SQL (press Ctrl+D when done):")
        down_sql = sys.stdin.read()
        create_migration(args.create, up_sql, down_sql)
    elif args.initial:
        if create_initial_migration():
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        migration_status()