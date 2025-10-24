"""Simple database migration system without Alembic."""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Column, DateTime, Integer, String, text
from sqlalchemy.orm import Session

from .database import Base, engine

logger = logging.getLogger(__name__)


class Migration(Base):
    """Track applied migrations."""

    __tablename__ = "migrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    applied_at = Column(DateTime, default=lambda: datetime.now(UTC))
    checksum = Column(String(64), nullable=True)  # Optional: verify migration hasn't changed


class MigrationRunner:
    """Simple migration runner."""

    def __init__(self, migrations_dir: str | Path | None = None):
        self.migrations_dir = Path(migrations_dir) if migrations_dir else Path(__file__).parent / "migrations"
        self.migrations_dir.mkdir(exist_ok=True)

    def ensure_migrations_table(self) -> None:
        """Create migrations table if it doesn't exist."""
        try:
            # Create migrations table
            Migration.__table__.create(bind=engine, checkfirst=True)
        except Exception as e:
            logger.error(f"Failed to create migrations table: {e}")
            raise

    def get_applied_migrations(self, session: Session) -> set[str]:
        """Get list of applied migration names."""
        try:
            applied = session.query(Migration.name).all()
            return {name[0] for name in applied}
        except Exception:
            # If table doesn't exist yet, return empty set
            return set()

    def get_pending_migrations(self, session: Session) -> list[Path]:
        """Get list of pending migration files."""
        if not self.migrations_dir.exists():
            return []

        applied = self.get_applied_migrations(session)

        # Find all .sql files in migrations directory
        migration_files = sorted(self.migrations_dir.glob("*.sql"))

        # Filter out already applied migrations
        pending = []
        for file_path in migration_files:
            migration_name = file_path.stem
            if migration_name not in applied:
                pending.append(file_path)

        return pending

    def run_migration(self, session: Session, migration_file: Path) -> None:
        """Run a single migration file."""
        migration_name = migration_file.stem

        try:
            # Read migration content
            sql_content = migration_file.read_text(encoding="utf-8")

            # Skip empty files
            if not sql_content.strip():
                logger.warning(f"Skipping empty migration: {migration_name}")
                return

            logger.info(f"Running migration: {migration_name}")

            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

            for statement in statements:
                try:
                    session.execute(text(statement))
                except Exception:
                    logger.error(f"Failed to execute statement in {migration_name}: {statement[:100]}...")
                    raise

            # Record successful migration
            migration_record = Migration(name=migration_name, applied_at=datetime.now(UTC))
            session.add(migration_record)
            session.commit()

            logger.info(f"✅ Migration {migration_name} completed successfully")

        except Exception as e:
            session.rollback()
            logger.error(f"❌ Migration {migration_name} failed: {e}")
            raise

    def run_all_pending(self, session: Session) -> None:
        """Run all pending migrations."""
        self.ensure_migrations_table()

        pending = self.get_pending_migrations(session)

        if not pending:
            logger.info("✅ No pending migrations")
            return

        logger.info(f"Found {len(pending)} pending migration(s)")

        for migration_file in pending:
            self.run_migration(session, migration_file)

        logger.info(f"✅ All {len(pending)} migration(s) completed successfully")

    def create_migration(self, name: str, content: str = "") -> Path:
        """Create a new migration file with timestamp prefix."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.sql"
        file_path = self.migrations_dir / filename

        # Create with template content if not provided
        if not content:
            content = f"""-- Migration: {name}
-- Created: {datetime.now(UTC).isoformat()}

-- Add your SQL statements here
-- Example:
-- ALTER TABLE agents ADD COLUMN new_field VARCHAR(255);

"""

        file_path.write_text(content, encoding="utf-8")
        logger.info(f"Created migration file: {file_path}")
        return file_path


def run_migrations() -> None:
    """Run all pending migrations. Called on app startup."""
    from .database import SessionLocal

    runner = MigrationRunner()

    with SessionLocal() as session:
        try:
            runner.run_all_pending(session)
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise


# CLI helper functions
def create_migration(name: str, content: str = "") -> Path:
    """Create a new migration file."""
    runner = MigrationRunner()
    return runner.create_migration(name, content)


def show_migration_status() -> dict[str, Any]:
    """Show migration status."""
    from .database import SessionLocal

    runner = MigrationRunner()

    with SessionLocal() as session:
        runner.ensure_migrations_table()
        applied = runner.get_applied_migrations(session)
        pending = runner.get_pending_migrations(session)

        return {
            "applied_count": len(applied),
            "applied_migrations": sorted(applied),
            "pending_count": len(pending),
            "pending_migrations": [p.name for p in pending],
        }
