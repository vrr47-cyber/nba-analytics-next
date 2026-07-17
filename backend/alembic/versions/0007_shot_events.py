"""Add canonical provider-neutral shot events."""
from alembic import op

from backend.app.database.models import Base

revision = "0007_shot_events"
down_revision = "0006_play_by_play_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.tables["shots"].create(bind=bind, checkfirst=True)
    op.execute("INSERT INTO schema_versions (version) VALUES ('phase10a-canonical-shots') ON CONFLICT (version) DO NOTHING")


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.tables["shots"].drop(bind=bind, checkfirst=True)
