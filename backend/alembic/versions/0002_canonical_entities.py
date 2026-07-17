"""Add canonical entity and coverage tables."""
from alembic import op

from backend.app.database.models import Base

revision = "0002_canonical_entities"
down_revision = "0001_phase1_foundation"
branch_labels = None
depends_on = None

CANONICAL_TABLES = [
    "coverage_evaluations", "standings_snapshots", "player_game_stats", "team_game_stats",
    "roster_snapshots", "game_provider_ids", "games", "player_provider_ids",
    "team_provider_ids", "players", "teams", "competitions", "seasons", "leagues",
]


def upgrade() -> None:
    bind = op.get_bind()
    for name in reversed(CANONICAL_TABLES):
        Base.metadata.tables[name].create(bind=bind, checkfirst=True)
    op.execute("INSERT INTO schema_versions (version) VALUES ('phase2a-canonical-entities') ON CONFLICT (version) DO NOTHING")


def downgrade() -> None:
    bind = op.get_bind()
    for name in CANONICAL_TABLES:
        Base.metadata.tables[name].drop(bind=bind, checkfirst=True)
