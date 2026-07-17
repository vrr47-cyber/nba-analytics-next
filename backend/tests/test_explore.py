from uuid import uuid4
from unittest.mock import MagicMock, patch

import pytest

from backend.app.domain.coverage import Coverage
from backend.app.schemas.envelope import Provenance
from backend.app.schemas.explore import ExploreSection
from backend.app.schemas.players import PlayerSummary, PublicationDecision as PlayerPublication
from backend.app.schemas.teams import TeamMetrics, TeamSummary, PublicationDecision as TeamPublication
from backend.app.services.explore import ExploreError, build_explore


def test_explore_composes_team_player_services_and_bounded_recent_games() -> None:
    team = TeamSummary(id=uuid4(), name="Fixture Team", abbreviation="FIX", conference=None, metrics=TeamMetrics())
    player = PlayerSummary(id=uuid4(), name="Fixture Player", position=None, team_attribution={"state": "unavailable"}, metrics={})
    team_coverage = Coverage(included_entities=1, reason="fixture")
    player_coverage = Coverage(included_entities=1, reason="fixture")
    provenance = Provenance(synthetic=True)
    recent = ExploreSection[list[object]](data=[], coverage=Coverage(reason="fixture"), publication={"publishable": False, "code": "synthetic_fixture", "reason": "fixture"}, provenance=provenance)
    session = MagicMock()
    with patch("backend.app.services.explore.team_summaries", return_value=([team], team_coverage, TeamPublication(publishable=False, code="synthetic_fixture", reason="fixture"), provenance)) as teams, patch("backend.app.services.explore.player_summaries", return_value=([player], player_coverage, PlayerPublication(publishable=False, code="synthetic_fixture", reason="fixture"), provenance)) as players, patch("backend.app.services.explore._recent_games", return_value=recent) as games:
        data, _, publication, _ = build_explore(session, "2099-00", "regular", 4, 5, 5)
    teams.assert_called_once_with(session, "2099-00", "regular", None, None, "name", False, 4)
    players.assert_called_once()
    games.assert_called_once()
    assert len(data.featured_teams.data) == 1
    assert len(data.featured_players.data) == 1
    assert publication.publishable is False


def test_explore_limits_are_bounded() -> None:
    with pytest.raises(ExploreError, match="between 1 and 10"):
        build_explore(MagicMock(), None, None, 11, 5, 5)
