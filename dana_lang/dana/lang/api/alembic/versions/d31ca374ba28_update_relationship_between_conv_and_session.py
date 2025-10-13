"""Update relationship between InterviewSession and Conversation

Revision ID: d31ca374ba28
Revises: 4470403318b6
Create Date: 2025-10-13 15:15:23.198035

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d31ca374ba28"
down_revision: Union[str, Sequence[str], None] = "4470403318b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - migrate from InterviewSession.conversation_id to Conversation.session_id (one-to-one)."""

    # Get database connection
    conn = op.get_bind()

    # Migrate data: Set Conversation.session_id based on InterviewSession.conversation_id
    conn.execute(
        sa.text("""
        UPDATE conversations_v2
        SET session_id = interview_sessions.id
        FROM interview_sessions
        WHERE interview_sessions.conversation_id = conversations_v2.id
        AND conversations_v2.session_id IS NULL
    """)
    )

    # For SQLite, we need to recreate the table to drop a column with foreign key
    # Check if conversation_id column exists before trying to drop it
    inspector = sa.inspect(conn)
    existing_columns = [col["name"] for col in inspector.get_columns("interview_sessions")]

    if "conversation_id" in existing_columns:
        # Create new table without conversation_id
        op.create_table(
            "interview_sessions_new",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("interview_template_id", sa.Integer(), nullable=False),
            sa.Column("session_name", sa.String(), nullable=True),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("interviewee_name", sa.String(), nullable=True),
            sa.Column("interviewee_role", sa.String(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["interview_template_id"],
                ["interview_templates.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )

        # Copy data from old table to new table (excluding conversation_id)
        conn.execute(
            sa.text("""
            INSERT INTO interview_sessions_new 
            (id, interview_template_id, session_name, status, interviewee_name, 
             interviewee_role, metadata, started_at, completed_at, created_at, updated_at)
            SELECT id, interview_template_id, session_name, status, interviewee_name,
                   interviewee_role, metadata, started_at, completed_at, created_at, updated_at
            FROM interview_sessions
        """)
        )

        # Drop old table
        op.drop_table("interview_sessions")

        # Rename new table
        op.rename_table("interview_sessions_new", "interview_sessions")

        # Recreate indexes
        op.create_index("ix_interview_sessions_id", "interview_sessions", ["id"], unique=False)
        op.create_index("ix_interview_sessions_interview_template_id", "interview_sessions", ["interview_template_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema - restore InterviewSession.conversation_id"""

    # For SQLite, we need to recreate the table to add a column with foreign key
    conn = op.get_bind()

    # Create new table with conversation_id column
    op.create_table(
        "interview_sessions_new",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("interview_template_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=True),
        sa.Column("session_name", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("interviewee_name", sa.String(), nullable=True),
        sa.Column("interviewee_role", sa.String(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["interview_template_id"],
            ["interview_templates.id"],
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations_v2.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Copy data from old table to new table
    conn.execute(
        sa.text("""
        INSERT INTO interview_sessions_new 
        (id, interview_template_id, session_name, status, interviewee_name, 
         interviewee_role, metadata, started_at, completed_at, created_at, updated_at)
        SELECT id, interview_template_id, session_name, status, interviewee_name,
               interviewee_role, metadata, started_at, completed_at, created_at, updated_at
        FROM interview_sessions
    """)
    )

    # Migrate data back: Set conversation_id based on Conversation.session_id
    conn.execute(
        sa.text("""
        UPDATE interview_sessions_new
        SET conversation_id = conversations_v2.id
        FROM conversations_v2
        WHERE conversations_v2.session_id = interview_sessions_new.id
    """)
    )

    # Clear session_id from conversations
    conn.execute(
        sa.text("""
        UPDATE conversations_v2
        SET session_id = NULL
        WHERE session_id IN (SELECT id FROM interview_sessions)
    """)
    )

    # Drop old table
    op.drop_table("interview_sessions")

    # Rename new table
    op.rename_table("interview_sessions_new", "interview_sessions")

    # Recreate indexes
    op.create_index("ix_interview_sessions_id", "interview_sessions", ["id"], unique=False)
    op.create_index("ix_interview_sessions_interview_template_id", "interview_sessions", ["interview_template_id"], unique=False)
    op.create_index("ix_interview_sessions_conversation_id", "interview_sessions", ["conversation_id"], unique=False)
