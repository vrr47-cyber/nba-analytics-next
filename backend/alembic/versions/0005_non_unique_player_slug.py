"""Make player slugs descriptive fields rather than identity constraints."""
from alembic import op
import sqlalchemy as sa

revision = "0005_non_unique_player_slug"
down_revision = "0004_league_provider_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TABLE players DROP CONSTRAINT IF EXISTS players_slug_key"))
    op.execute(sa.text("ALTER TABLE players DROP CONSTRAINT IF EXISTS uq_players_slug"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_players_slug ON players (slug)"))
    op.execute("INSERT INTO schema_versions (version) VALUES ('phase3b-player-roster-identity') ON CONFLICT (version) DO NOTHING")


def downgrade() -> None:
    bind = op.get_bind()
    duplicate = bind.execute(sa.text("SELECT slug FROM players GROUP BY slug HAVING COUNT(*) > 1 LIMIT 1")).first()
    if duplicate is not None:
        raise RuntimeError("cannot restore global player slug uniqueness while duplicate slugs exist")
    op.drop_index("ix_players_slug", table_name="players")
    op.create_unique_constraint("players_slug_key", "players", ["slug"])
