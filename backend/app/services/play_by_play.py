from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import CoverageEvaluation, Game, GameProviderId, PlayByPlayEvent, PlayByPlayEventParticipant, Player, PlayerProviderId, RosterSnapshot, SourceRun, Team, TeamGameStats, TeamProviderId
from backend.app.domain.play_by_play import NormalizedPlayByPlayEvent, NormalizedPlayByPlayPayload, ParticipantRole, PlayEventType


class PlayByPlayIngestionError(ValueError):
    pass


@dataclass(frozen=True)
class EventCounts:
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    removed: int = 0


@dataclass(frozen=True)
class _ResolvedParticipant:
    role: str
    team_id: UUID | None
    player_id: UUID | None


@dataclass(frozen=True)
class _Prepared:
    game: Game
    events: tuple[tuple[NormalizedPlayByPlayEvent, tuple[_ResolvedParticipant, ...], PlayByPlayEvent | None], ...]
    existing: dict[str, PlayByPlayEvent]
    counts: EventCounts


_ROLE_RULES: dict[PlayEventType, frozenset[ParticipantRole]] = {
    PlayEventType.GAME_START: frozenset(),
    PlayEventType.PERIOD_START: frozenset(),
    PlayEventType.MADE_FIELD_GOAL: frozenset({ParticipantRole.SCORING_TEAM, ParticipantRole.SHOOTER}),
    PlayEventType.MISSED_FIELD_GOAL: frozenset({ParticipantRole.SHOOTING_TEAM, ParticipantRole.SHOOTER}),
    PlayEventType.FREE_THROW: frozenset({ParticipantRole.SHOOTING_TEAM, ParticipantRole.SHOOTER}),
    PlayEventType.REBOUND: frozenset({ParticipantRole.REBOUND_TEAM, ParticipantRole.REBOUNDER}),
    PlayEventType.TURNOVER: frozenset({ParticipantRole.COMMITTING_TEAM, ParticipantRole.COMMITTING_PLAYER}),
    PlayEventType.FOUL: frozenset({ParticipantRole.COMMITTING_TEAM, ParticipantRole.COMMITTING_PLAYER}),
    PlayEventType.SUBSTITUTION: frozenset({ParticipantRole.ENTERING_PLAYER, ParticipantRole.EXITING_PLAYER}),
    PlayEventType.TIMEOUT: frozenset({ParticipantRole.TIMEOUT_TEAM}),
    PlayEventType.JUMP_BALL: frozenset({ParticipantRole.JUMP_BALL_PLAYER_ONE, ParticipantRole.JUMP_BALL_PLAYER_TWO}),
    PlayEventType.PERIOD_END: frozenset(),
    PlayEventType.GAME_END: frozenset(),
}

_TEAM_ROLES = {ParticipantRole.SCORING_TEAM, ParticipantRole.SHOOTING_TEAM, ParticipantRole.REBOUND_TEAM, ParticipantRole.COMMITTING_TEAM, ParticipantRole.TIMEOUT_TEAM}
_PLAYER_ROLES = {ParticipantRole.SHOOTER, ParticipantRole.REBOUNDER, ParticipantRole.COMMITTING_PLAYER, ParticipantRole.ENTERING_PLAYER, ParticipantRole.EXITING_PLAYER, ParticipantRole.JUMP_BALL_PLAYER_ONE, ParticipantRole.JUMP_BALL_PLAYER_TWO}


def _clock_is_valid(period: int, clock: int) -> bool:
    return 0 <= clock <= (720 if period <= 4 else 300)


def _participant_key(participant: _ResolvedParticipant) -> tuple[str, str]:
    return participant.role, str(participant.team_id or participant.player_id)


def _semantic(event: NormalizedPlayByPlayEvent, participants: tuple[_ResolvedParticipant, ...]) -> tuple[Any, ...]:
    return (event.sequence_number, event.period, event.clock_seconds_remaining, event.event_type.value, event.outcome, event.points_value, event.home_score, event.away_score, tuple(sorted(_participant_key(participant) for participant in participants)))


def _db_semantic(event: PlayByPlayEvent, participants: list[PlayByPlayEventParticipant]) -> tuple[Any, ...]:
    return (event.sequence_number, event.period, event.clock_seconds_remaining, event.event_type, event.outcome, event.points_value, event.home_score, event.away_score, tuple(sorted((participant.role, str(participant.team_id or participant.player_id)) for participant in participants)))


def _resolve_team(session: Session, provider: str, external_id: str) -> Team:
    mapping = session.scalar(select(TeamProviderId).where(TeamProviderId.provider_name == provider, TeamProviderId.external_id == external_id))
    if mapping is None:
        raise PlayByPlayIngestionError(f"missing canonical team mapping: {provider}/{external_id}")
    team = session.get(Team, mapping.team_id)
    if team is None:
        raise PlayByPlayIngestionError(f"team mapping points to missing canonical team: {provider}/{external_id}")
    return team


def _resolve_player(session: Session, provider: str, external_id: str) -> Player:
    mapping = session.scalar(select(PlayerProviderId).where(PlayerProviderId.provider_name == provider, PlayerProviderId.external_id == external_id))
    if mapping is None:
        raise PlayByPlayIngestionError(f"missing canonical player mapping: {provider}/{external_id}")
    player = session.get(Player, mapping.player_id)
    if player is None:
        raise PlayByPlayIngestionError(f"player mapping points to missing canonical player: {provider}/{external_id}")
    return player


def _player_roster_team(session: Session, game: Game, player_id: UUID) -> UUID:
    snapshots = list(session.scalars(select(RosterSnapshot).where(RosterSnapshot.season_id == game.season_id, RosterSnapshot.competition_id == game.competition_id, RosterSnapshot.player_id == player_id, RosterSnapshot.snapshot_at <= datetime.combine(game.game_date, datetime.max.time(), tzinfo=timezone.utc))))
    if not snapshots:
        raise PlayByPlayIngestionError("player participant has no roster observation on or before game date")
    latest = max(row.snapshot_at for row in snapshots)
    teams = {row.team_id for row in snapshots if row.snapshot_at == latest}
    if len(teams) != 1:
        raise PlayByPlayIngestionError("player participant has ambiguous roster team attribution")
    return next(iter(teams))


def _resolve_participants(session: Session, *, provider: str, game: Game, event: NormalizedPlayByPlayEvent) -> tuple[_ResolvedParticipant, ...]:
    required = _ROLE_RULES[event.event_type]
    roles = [participant.role for participant in event.participants]
    if len(roles) != len(set(roles)):
        raise PlayByPlayIngestionError(f"duplicate participant roles for event {event.provider_event_id}")
    if set(roles) != required:
        raise PlayByPlayIngestionError(f"invalid participant roles for event {event.provider_event_id}: expected {sorted(role.value for role in required)}")
    resolved: list[_ResolvedParticipant] = []
    for participant in event.participants:
        if participant.role in _TEAM_ROLES:
            if participant.team_external_id is None:
                raise PlayByPlayIngestionError(f"team role requires team mapping for event {event.provider_event_id}")
            team = _resolve_team(session, provider, participant.team_external_id)
            if team.id not in {game.home_team_id, game.away_team_id}:
                raise PlayByPlayIngestionError(f"event team is not a canonical game participant: {event.provider_event_id}")
            resolved.append(_ResolvedParticipant(participant.role.value, team.id, None))
        elif participant.role in _PLAYER_ROLES:
            if participant.player_external_id is None:
                raise PlayByPlayIngestionError(f"player role requires player mapping for event {event.provider_event_id}")
            player = _resolve_player(session, provider, participant.player_external_id)
            roster_team = _player_roster_team(session, game, player.id)
            if roster_team not in {game.home_team_id, game.away_team_id}:
                raise PlayByPlayIngestionError(f"event player is not attributed to a canonical game participant: {event.provider_event_id}")
            resolved.append(_ResolvedParticipant(participant.role.value, None, player.id))
    teams_by_role = {participant.role: participant.team_id for participant in resolved if participant.team_id is not None}
    players_by_role = {participant.role: participant.player_id for participant in resolved if participant.player_id is not None}
    for player_role, team_role in (("shooter", "scoring_team"), ("shooter", "shooting_team"), ("rebounder", "rebound_team"), ("committing_player", "committing_team")):
        if player_role in players_by_role and team_role in teams_by_role and _player_roster_team(session, game, players_by_role[player_role]) != teams_by_role[team_role]:
            raise PlayByPlayIngestionError(f"player and team participant attribution conflict: {event.provider_event_id}")
    if event.event_type == PlayEventType.SUBSTITUTION:
        entering = _player_roster_team(session, game, players_by_role["entering_player"])
        exiting = _player_roster_team(session, game, players_by_role["exiting_player"])
        if entering != exiting:
            raise PlayByPlayIngestionError(f"substitution players must share a canonical team: {event.provider_event_id}")
    if event.event_type == PlayEventType.JUMP_BALL and _player_roster_team(session, game, players_by_role["jump_ball_player_one"]) == _player_roster_team(session, game, players_by_role["jump_ball_player_two"]):
        raise PlayByPlayIngestionError(f"jump-ball players must represent opposing teams: {event.provider_event_id}")
    return tuple(resolved)


def _validate_score_progression(game: Game, team_stats: list[TeamGameStats], events: list[tuple[NormalizedPlayByPlayEvent, tuple[_ResolvedParticipant, ...]]]) -> None:
    if len(team_stats) != 2 or {row.team_id for row in team_stats} != {game.home_team_id, game.away_team_id}:
        raise PlayByPlayIngestionError("complete play-by-play requires both scoped team box-score rows")
    stats_points = {row.team_id: row.points for row in team_stats}
    if stats_points[game.home_team_id] != game.home_final_score or stats_points[game.away_team_id] != game.away_final_score:
        raise PlayByPlayIngestionError("canonical team box scores do not match canonical final game scores")
    if not events or events[0][0].event_type != PlayEventType.GAME_START or events[0][0].home_score != 0 or events[0][0].away_score != 0 or events[-1][0].event_type != PlayEventType.GAME_END:
        raise PlayByPlayIngestionError("complete play-by-play must start at 0-0 game_start and end with game_end")
    periods = sorted({event.period for event, _ in events})
    if periods != list(range(1, periods[-1] + 1)):
        raise PlayByPlayIngestionError("complete play-by-play periods must be contiguous")
    for period in periods:
        period_events = [event for event, _ in events if event.period == period]
        starts_correctly = period_events[0].event_type == PlayEventType.PERIOD_START or (period == 1 and len(period_events) > 1 and period_events[0].event_type == PlayEventType.GAME_START and period_events[1].event_type == PlayEventType.PERIOD_START)
        ends_correctly = period_events[-1].event_type == PlayEventType.PERIOD_END or (period == periods[-1] and len(period_events) > 1 and period_events[-2].event_type == PlayEventType.PERIOD_END and period_events[-1].event_type == PlayEventType.GAME_END)
        if not starts_correctly or not ends_correctly:
            raise PlayByPlayIngestionError(f"period {period} must have explicit start and end events")
    previous = (0, 0)
    scoring_totals: dict[UUID, int] = defaultdict(int)
    for event, participants in events:
        if not _clock_is_valid(event.period, event.clock_seconds_remaining):
            raise PlayByPlayIngestionError(f"invalid period clock for event {event.provider_event_id}")
        current = (event.home_score, event.away_score)
        delta = (current[0] - previous[0], current[1] - previous[1])
        if delta[0] < 0 or delta[1] < 0 or (delta[0] and delta[1]):
            raise PlayByPlayIngestionError(f"non-monotonic or ambiguous score progression: {event.provider_event_id}")
        expected = 0
        scoring_team: UUID | None = None
        if event.event_type in {PlayEventType.MADE_FIELD_GOAL, PlayEventType.FREE_THROW}:
            if event.outcome != "made":
                raise PlayByPlayIngestionError(f"made scoring event requires made outcome: {event.provider_event_id}")
            expected = event.points_value or 0
            scoring_team = next((participant.team_id for participant in participants if participant.role in {ParticipantRole.SCORING_TEAM.value, ParticipantRole.SHOOTING_TEAM.value}), None)
            if event.event_type == PlayEventType.MADE_FIELD_GOAL and expected not in {2, 3}:
                raise PlayByPlayIngestionError(f"made field goal requires two or three points: {event.provider_event_id}")
            if event.event_type == PlayEventType.FREE_THROW and expected != 1:
                raise PlayByPlayIngestionError(f"made free throw requires one point: {event.provider_event_id}")
        elif event.event_type == PlayEventType.MISSED_FIELD_GOAL:
            if event.outcome != "missed" or event.points_value not in {None, 0}:
                raise PlayByPlayIngestionError(f"missed field goal cannot score: {event.provider_event_id}")
        elif event.event_type == PlayEventType.GAME_END:
            expected = 0
        elif event.points_value not in {None, 0}:
            raise PlayByPlayIngestionError(f"non-scoring event cannot have points: {event.provider_event_id}")
        if expected:
            if scoring_team == game.home_team_id and delta != (expected, 0):
                raise PlayByPlayIngestionError(f"home scoring delta does not match event: {event.provider_event_id}")
            if scoring_team == game.away_team_id and delta != (0, expected):
                raise PlayByPlayIngestionError(f"away scoring delta does not match event: {event.provider_event_id}")
            if scoring_team is None:
                raise PlayByPlayIngestionError(f"scoring event has no resolved scoring team: {event.provider_event_id}")
            scoring_totals[scoring_team] += expected
        elif delta != (0, 0):
            raise PlayByPlayIngestionError(f"non-scoring event changed score: {event.provider_event_id}")
        previous = current
    if previous != (game.home_final_score, game.away_final_score) or scoring_totals[game.home_team_id] != game.home_final_score or scoring_totals[game.away_team_id] != game.away_final_score:
        raise PlayByPlayIngestionError("play-by-play final scoring totals do not match canonical final scores")


def _prepare(session: Session, *, provider: str, payload: NormalizedPlayByPlayPayload, correction_mode: bool) -> _Prepared:
    mapping = session.scalar(select(GameProviderId).where(GameProviderId.provider_name == provider, GameProviderId.external_id == payload.game_external_id))
    if mapping is None:
        raise PlayByPlayIngestionError(f"missing canonical game mapping: {provider}/{payload.game_external_id}")
    game = session.get(Game, mapping.game_id)
    if game is None:
        raise PlayByPlayIngestionError("game mapping points to missing canonical game")
    if game.status != "final":
        raise PlayByPlayIngestionError("play-by-play requires a canonical final game")
    if not payload.complete_payload:
        raise PlayByPlayIngestionError("Phase 6 requires a complete game payload")
    ids = [event.provider_event_id for event in payload.events]
    sequences = [event.sequence_number for event in payload.events]
    if len(ids) != len(set(ids)):
        raise PlayByPlayIngestionError("duplicate provider event IDs in payload")
    if len(sequences) != len(set(sequences)):
        raise PlayByPlayIngestionError("duplicate provider event sequences in payload")
    ordered = sorted(payload.events, key=lambda event: event.sequence_number)
    if [event.sequence_number for event in ordered] != list(range(1, len(ordered) + 1)):
        raise PlayByPlayIngestionError("complete payload sequences must be contiguous and start at one")
    if any(event.game_external_id != payload.game_external_id for event in ordered):
        raise PlayByPlayIngestionError("event game identity does not match payload game")
    prepared_normalized = tuple((event, _resolve_participants(session, provider=provider, game=game, event=event)) for event in ordered)
    team_stats = list(session.scalars(select(TeamGameStats).where(TeamGameStats.game_id == game.id)))
    _validate_score_progression(game, team_stats, list(prepared_normalized))
    existing_rows = list(session.scalars(select(PlayByPlayEvent).where(PlayByPlayEvent.game_id == game.id, PlayByPlayEvent.provider_name == provider)))
    existing = {row.provider_event_id: row for row in existing_rows}
    if len(existing) != len(existing_rows):
        raise PlayByPlayIngestionError("duplicate provider event identities already exist")
    prepared: list[tuple[NormalizedPlayByPlayEvent, tuple[_ResolvedParticipant, ...], PlayByPlayEvent | None]] = []
    updated = unchanged = 0
    incoming_ids = set(ids)
    for event, participants in prepared_normalized:
        current = existing.get(event.provider_event_id)
        if current is None:
            prepared.append((event, participants, None))
            continue
        current_participants = list(session.scalars(select(PlayByPlayEventParticipant).where(PlayByPlayEventParticipant.event_id == current.id)))
        if _semantic(event, participants) == _db_semantic(current, current_participants):
            unchanged += 1
        else:
            if not correction_mode:
                raise PlayByPlayIngestionError(f"event correction requires correction mode: {event.provider_event_id}")
            updated += 1
        prepared.append((event, participants, current))
    removed = len(set(existing) - incoming_ids)
    if (removed or any(item[2] is None for item in prepared)) and existing and not correction_mode:
        raise PlayByPlayIngestionError("event additions or removals require correction mode")
    if not existing:
        inserted = len(prepared)
    else:
        inserted = sum(item[2] is None for item in prepared)
    return _Prepared(game, tuple(prepared), existing, EventCounts(inserted, updated, unchanged, removed))


def validate_play_by_play_reference(session: Session, *, provider: str, payload: NormalizedPlayByPlayPayload, correction_mode: bool = False) -> dict[str, Any]:
    prepared = _prepare(session, provider=provider, payload=payload, correction_mode=correction_mode)
    return {"mutated": False, "counts": prepared.counts.__dict__, "source_run_created": False, "publication_status": "withheld"}


def _persist_participants(session: Session, event_id: UUID, participants: tuple[_ResolvedParticipant, ...], source_run_id: UUID) -> None:
    for participant in participants:
        session.add(PlayByPlayEventParticipant(event_id=event_id, role=participant.role, team_id=participant.team_id, player_id=participant.player_id))


def ingest_play_by_play_reference(session: Session, *, provider: str, payload: NormalizedPlayByPlayPayload, schema_version: str, normalized_payload_fingerprint: str, synthetic: bool, correction_mode: bool = False) -> dict[str, Any]:
    prepared = _prepare(session, provider=provider, payload=payload, correction_mode=correction_mode)
    now = datetime.now(timezone.utc)
    source_run = SourceRun(id=uuid4(), provider_name=provider, status="running", started_at=now, metadata_json={"operation": "play_by_play", "load_timestamp": now.isoformat(), "schema_version": schema_version, "record_count": len(payload.events), "normalized_payload_fingerprint": normalized_payload_fingerprint, "synthetic": synthetic, "correction_mode": correction_mode})
    session.add(source_run)
    session.flush()
    try:
        retained = {item[2].provider_event_id: item[2] for item in prepared.events if item[2] is not None}
        removed = set(prepared.existing) - set(retained)
        for provider_event_id in removed:
            old = prepared.existing[provider_event_id]
            session.query(PlayByPlayEventParticipant).filter_by(event_id=old.id).delete(synchronize_session=False)
            session.delete(old)
        session.flush()
        sequence_changed = any(old.sequence_number != event.sequence_number for event, _, old in prepared.events if old is not None)
        if sequence_changed:
            base = max([event.sequence_number for event, _, _ in prepared.events] + [row.sequence_number for row in prepared.existing.values()] + [1000]) + len(prepared.existing) + len(prepared.events) + 1
            for index, old in enumerate(retained.values()):
                old.sequence_number = base + index
            session.flush()
        for event, participants, existing_event in prepared.events:
            values = {"game_id": prepared.game.id, "provider_name": provider, "provider_event_id": event.provider_event_id, "sequence_number": event.sequence_number, "period": event.period, "clock_seconds_remaining": event.clock_seconds_remaining, "event_type": event.event_type.value, "outcome": event.outcome, "points_value": event.points_value, "home_score": event.home_score, "away_score": event.away_score, "source_updated_at": datetime.fromisoformat(event.source.source_updated_at) if event.source.source_updated_at else now, "source_run_id": source_run.id}
            if existing_event is None:
                new_event = PlayByPlayEvent(**values)
                session.add(new_event)
                session.flush()
                _persist_participants(session, new_event.id, participants, source_run.id)
            else:
                for key, value in values.items():
                    if key not in {"game_id", "provider_name", "provider_event_id"}:
                        setattr(existing_event, key, value)
                current_participants = list(session.scalars(select(PlayByPlayEventParticipant).where(PlayByPlayEventParticipant.event_id == existing_event.id)))
                if _semantic(event, participants) != _db_semantic(existing_event, current_participants):
                    session.query(PlayByPlayEventParticipant).filter_by(event_id=existing_event.id).delete(synchronize_session=False)
                    _persist_participants(session, existing_event.id, participants, source_run.id)
        blocking = ["synthetic_fixture"] if synthetic else []
        session.add(CoverageEvaluation(dataset_name="play_by_play", evaluated_at=now, included_games=1, expected_games=1, included_entities=len(prepared.events), expected_entities=len(prepared.events), coverage_ratio=1, completeness_status="complete", publication_status="withheld", blocking_reasons=blocking, details={"provider": provider, "game_id": str(prepared.game.id), "source_run_id": str(source_run.id), "complete_payload": True, "event_counts": prepared.counts.__dict__}, policy_version="phase6-play-by-play-v1"))
        source_run.status = "succeeded"
        source_run.completed_at = now
        source_run.metadata_json = {**(source_run.metadata_json or {}), "events_inserted": prepared.counts.inserted, "events_updated": prepared.counts.updated, "events_unchanged": prepared.counts.unchanged, "events_removed": prepared.counts.removed, "publication_status": "withheld"}
        session.flush()
    except Exception as exc:
        source_run.status = "failed"
        source_run.completed_at = datetime.now(timezone.utc)
        source_run.error_message = str(exc)
        session.flush()
        raise
    return {"source_run_id": str(source_run.id), "counts": prepared.counts.__dict__, "publication_status": "withheld", "synthetic": synthetic, "release_created": False, "source_run_status": "succeeded"}
