"""Create provider-neutral foundation tables."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_phase1_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("schema_versions", sa.Column("version", sa.String(100), primary_key=True), sa.Column("applied_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("source_runs", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("provider_name", sa.String(100), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("started_at", sa.DateTime(timezone=True), nullable=False), sa.Column("completed_at", sa.DateTime(timezone=True)), sa.Column("metadata_json", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")), sa.Column("error_message", sa.Text))
    op.create_table("dataset_releases", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("dataset_name", sa.String(100), nullable=False), sa.Column("version", sa.String(100), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("source_run_id", postgresql.UUID(as_uuid=True)), sa.Column("coverage_json", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")), sa.Column("provenance_json", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")), sa.Column("released_at", sa.DateTime(timezone=True)))
    op.create_table("model_versions", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("model_name", sa.String(100), nullable=False), sa.Column("version", sa.String(100), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("metadata_json", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.execute(sa.text("INSERT INTO schema_versions (version) VALUES ('phase1-foundation')"))


def downgrade() -> None:
    op.drop_table("model_versions")
    op.drop_table("dataset_releases")
    op.drop_table("source_runs")
    op.drop_table("schema_versions")
