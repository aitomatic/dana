"""add_template_and_session_to_conversations

Revision ID: 4470403318b6
Revises: 695b54fda534
Create Date: 2025-10-13 14:08:06.846869

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4470403318b6"
down_revision: Union[str, Sequence[str], None] = "695b54fda534"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add template_id and session_id to conversations_v2.

    Note: Foreign key constraints are defined in SQLAlchemy models (ondelete='CASCADE').
    SQLite has limitations with ALTER TABLE and foreign keys, so we add columns and indexes here.
    """
    # Get connection to check if columns exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col["name"] for col in inspector.get_columns("conversations_v2")]

    # Add columns only if they don't exist
    if "template_id" not in existing_columns:
        op.add_column("conversations_v2", sa.Column("template_id", sa.Integer(), nullable=True))
    if "session_id" not in existing_columns:
        op.add_column("conversations_v2", sa.Column("session_id", sa.Integer(), nullable=True))

    # Get existing indexes
    existing_indexes = [idx["name"] for idx in inspector.get_indexes("conversations_v2")]

    # Add indexes only if they don't exist
    if "ix_conversations_v2_template_id" not in existing_indexes:
        op.create_index("ix_conversations_v2_template_id", "conversations_v2", ["template_id"], unique=False)
    if "ix_conversations_v2_session_id" not in existing_indexes:
        op.create_index("ix_conversations_v2_session_id", "conversations_v2", ["session_id"], unique=False)
    if "ix_conversations_v2_template_id_type" not in existing_indexes:
        op.create_index("ix_conversations_v2_template_id_type", "conversations_v2", ["template_id", "type"], unique=False)
    if "ix_conversations_v2_session_id_type" not in existing_indexes:
        op.create_index("ix_conversations_v2_session_id_type", "conversations_v2", ["session_id", "type"], unique=False)


def downgrade() -> None:
    """Downgrade schema - remove template_id and session_id from conversations_v2."""
    # Drop indexes
    op.drop_index("ix_conversations_v2_session_id_type", "conversations_v2")
    op.drop_index("ix_conversations_v2_template_id_type", "conversations_v2")
    op.drop_index("ix_conversations_v2_session_id", "conversations_v2")
    op.drop_index("ix_conversations_v2_template_id", "conversations_v2")

    # Drop columns
    op.drop_column("conversations_v2", "session_id")
    op.drop_column("conversations_v2", "template_id")
