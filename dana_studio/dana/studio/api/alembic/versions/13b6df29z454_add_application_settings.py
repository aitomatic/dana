"""Add application_settings table

Revision ID: 13b6df29z454_add_application_settings
Revises: c7cd1ef038b1
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "13b6df29z454_add_application_settings"
down_revision: Union[str, Sequence[str], None] = "c7cd1ef038b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create application_settings table
    op.create_table(
        "application_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("full_key", sa.String(), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("placeholders", sa.JSON(), nullable=True),
        sa.Column("placeholder_examples", sa.JSON(), nullable=True),
        sa.Column("default_value", sa.Text(), nullable=True),
        sa.Column("version", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("applies_to", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("full_key"),
    )
    op.create_index(op.f("ix_application_settings_category"), "application_settings", ["category"], unique=False)
    op.create_index(op.f("ix_application_settings_key"), "application_settings", ["key"], unique=False)
    op.create_index(op.f("ix_application_settings_full_key"), "application_settings", ["full_key"], unique=True)

    # Insert default template_generation.prompt setting
    # Import from shared/prompt_defaults to avoid duplication
    from dana.studio.api.shared.prompt_defaults import DEFAULT_PROMPTS
    from datetime import datetime, UTC
    import json

    # Get the config from DEFAULT_PROMPTS
    config = DEFAULT_PROMPTS["template_generation"]["prompt"]
    default_prompt = config["default_value"]
    placeholder_examples = config["placeholder_examples"]

    conn = op.get_bind()
    conn.execute(
        sa.text("""
            INSERT INTO application_settings (category, key, full_key, value, name, description, placeholders, placeholder_examples, default_value, version, created_at, updated_at, applies_to, is_active)
            VALUES (:category, :key, :full_key, :value, :name, :description, :placeholders, :placeholder_examples, :default_value, :version, :created_at, :updated_at, :applies_to, :is_active)
        """),
        {
            "category": "template_generation",
            "key": "prompt",
            "full_key": "template_generation.prompt",
            "value": default_prompt,
            "name": config["name"],
            "description": config["description"],
            "placeholders": json.dumps(config["placeholders"]),
            "placeholder_examples": json.dumps(placeholder_examples),
            "default_value": default_prompt,
            "version": "1.0.0",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "applies_to": "global",
            "is_active": True,
        },
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_application_settings_full_key"), table_name="application_settings")
    op.drop_index(op.f("ix_application_settings_key"), table_name="application_settings")
    op.drop_index(op.f("ix_application_settings_category"), table_name="application_settings")
    op.drop_table("application_settings")
