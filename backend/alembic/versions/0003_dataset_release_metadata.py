"""Add immutable dataset release metadata fields."""
from alembic import op
import sqlalchemy as sa

revision = "0003_dataset_release_metadata"
down_revision = "0002_canonical_entities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("dataset_releases", sa.Column("schema_version", sa.String(50), nullable=False, server_default="phase2b-v1"))
    op.add_column("dataset_releases", sa.Column("validation_status", sa.String(30), nullable=False, server_default="pending"))
    op.add_column("dataset_releases", sa.Column("publication_status", sa.String(30), nullable=False, server_default="withheld"))
    op.add_column("dataset_releases", sa.Column("manifest_checksum", sa.String(64), nullable=True))
    op.add_column("dataset_releases", sa.Column("manifest_reference", sa.Text(), nullable=True))
    op.add_column("dataset_releases", sa.Column("generating_commit", sa.String(64), nullable=True))


def downgrade() -> None:
    for name in ("generating_commit", "manifest_reference", "manifest_checksum", "publication_status", "validation_status", "schema_version"):
        op.drop_column("dataset_releases", name)
