"""Add canonical play-by-play event and participant tables."""
from alembic import op

from backend.app.database.models import Base

revision = "0006_play_by_play_events"
down_revision = "0005_non_unique_player_slug"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.tables["play_by_play_events"].create(bind=bind, checkfirst=True)
    Base.metadata.tables["play_by_play_event_participants"].create(bind=bind, checkfirst=True)
    op.execute("INSERT INTO schema_versions (version) VALUES ('phase6-play-by-play-events') ON CONFLICT (version) DO NOTHING")


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.tables["play_by_play_event_participants"].drop(bind=bind, checkfirst=True)
    Base.metadata.tables["play_by_play_events"].drop(bind=bind, checkfirst=True)
