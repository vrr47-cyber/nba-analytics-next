"""Add provider identity mappings for canonical leagues."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_league_provider_identity"
down_revision = "0003_dataset_release_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "league_provider_ids",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider_name", sa.String(100), nullable=False),
        sa.Column("external_id", sa.String(150), nullable=False),
        sa.Column("league_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leagues.id"), nullable=False),
        sa.Column("first_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("provider_name", "external_id", name="uq_league_provider_external"),
    )
    op.create_index("ix_league_provider_league", "league_provider_ids", ["league_id"])
    op.execute("INSERT INTO schema_versions (version) VALUES ('phase3a-league-provider-identity') ON CONFLICT (version) DO NOTHING")


def downgrade() -> None:
    op.drop_index("ix_league_provider_league", table_name="league_provider_ids")
    op.drop_table("league_provider_ids")
