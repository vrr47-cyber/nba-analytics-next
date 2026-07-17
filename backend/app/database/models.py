from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SchemaVersion(Base):
    __tablename__ = "schema_versions"
    version: Mapped[str] = mapped_column(String(100), primary_key=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SourceRun(Base):
    __tablename__ = "source_runs"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    provider_name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class DatasetRelease(Base):
    __tablename__ = "dataset_releases"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    dataset_name: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30))
    schema_version: Mapped[str] = mapped_column(String(50), default="phase2b-v1")
    validation_status: Mapped[str] = mapped_column(String(30), default="pending")
    publication_status: Mapped[str] = mapped_column(String(30), default="withheld")
    source_run_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    coverage_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    provenance_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    manifest_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    manifest_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    generating_commit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    model_name: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TimestampedModel(Base):
    __abstract__ = True
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class League(TimestampedModel):
    __tablename__ = "leagues"
    code: Mapped[str] = mapped_column(String(50), unique=True)
    display_name: Mapped[str] = mapped_column(String(150))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Season(TimestampedModel):
    __tablename__ = "seasons"
    league_id: Mapped[UUID] = mapped_column(ForeignKey("leagues.id"))
    season_code: Mapped[str] = mapped_column(String(7))
    display_label: Mapped[str] = mapped_column(String(100))
    start_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30))
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (UniqueConstraint("league_id", "season_code", name="uq_seasons_league_code"),)


class Competition(TimestampedModel):
    __tablename__ = "competitions"
    league_id: Mapped[UUID] = mapped_column(ForeignKey("leagues.id"))
    code: Mapped[str] = mapped_column(String(50))
    display_name: Mapped[str] = mapped_column(String(150))
    category: Mapped[str] = mapped_column(String(50))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("league_id", "code", name="uq_competitions_league_code"),)


class Team(TimestampedModel):
    __tablename__ = "teams"
    league_id: Mapped[UUID] = mapped_column(ForeignKey("leagues.id"))
    slug: Mapped[str] = mapped_column(String(100))
    full_name: Mapped[str] = mapped_column(String(150))
    short_name: Mapped[str] = mapped_column(String(100))
    abbreviation: Mapped[str] = mapped_column(String(8))
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    conference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    division: Mapped[str | None] = mapped_column(String(100), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    valid_from: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    __table_args__ = (UniqueConstraint("league_id", "slug", name="uq_teams_league_slug"),)


class Player(TimestampedModel):
    __tablename__ = "players"
    slug: Mapped[str] = mapped_column(String(100), index=True)
    full_name: Mapped[str] = mapped_column(String(150))
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    position: Mapped[str | None] = mapped_column(String(30), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ProviderIdentity(TimestampedModel):
    __abstract__ = True
    provider_name: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str] = mapped_column(String(150))
    first_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class TeamProviderId(ProviderIdentity):
    __tablename__ = "team_provider_ids"
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"))
    __table_args__ = (UniqueConstraint("provider_name", "external_id", name="uq_team_provider_external"),)


class LeagueProviderId(ProviderIdentity):
    __tablename__ = "league_provider_ids"
    league_id: Mapped[UUID] = mapped_column(ForeignKey("leagues.id"))
    __table_args__ = (UniqueConstraint("provider_name", "external_id", name="uq_league_provider_external"),)


class PlayerProviderId(ProviderIdentity):
    __tablename__ = "player_provider_ids"
    player_id: Mapped[UUID] = mapped_column(ForeignKey("players.id"))
    __table_args__ = (UniqueConstraint("provider_name", "external_id", name="uq_player_provider_external"),)


class Game(TimestampedModel):
    __tablename__ = "games"
    season_id: Mapped[UUID] = mapped_column(ForeignKey("seasons.id"))
    competition_id: Mapped[UUID] = mapped_column(ForeignKey("competitions.id"))
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    game_date: Mapped[date] = mapped_column(Date)
    home_team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"))
    away_team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"))
    status: Mapped[str] = mapped_column(String(30))
    home_final_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_final_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    neutral_site: Mapped[bool] = mapped_column(Boolean, default=False)
    official_external_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    archival_external_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_run_id: Mapped[UUID] = mapped_column(ForeignKey("source_runs.id"))
    __table_args__ = (CheckConstraint("home_team_id <> away_team_id", name="ck_games_distinct_teams"), CheckConstraint("home_final_score IS NULL OR home_final_score >= 0", name="ck_games_home_score_nonnegative"), CheckConstraint("away_final_score IS NULL OR away_final_score >= 0", name="ck_games_away_score_nonnegative"), Index("ix_games_season_date", "season_id", "game_date"))


class GameProviderId(ProviderIdentity):
    __tablename__ = "game_provider_ids"
    game_id: Mapped[UUID] = mapped_column(ForeignKey("games.id"))
    __table_args__ = (UniqueConstraint("provider_name", "external_id", name="uq_game_provider_external"),)


class RosterSnapshot(TimestampedModel):
    __tablename__ = "roster_snapshots"
    season_id: Mapped[UUID] = mapped_column(ForeignKey("seasons.id"))
    competition_id: Mapped[UUID | None] = mapped_column(ForeignKey("competitions.id"), nullable=True)
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"))
    player_id: Mapped[UUID] = mapped_column(ForeignKey("players.id"))
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    jersey_number: Mapped[str | None] = mapped_column(String(10), nullable=True)
    listed_position: Mapped[str | None] = mapped_column(String(30), nullable=True)
    roster_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_run_id: Mapped[UUID] = mapped_column(ForeignKey("source_runs.id"))
    __table_args__ = (UniqueConstraint("season_id", "competition_id", "team_id", "player_id", "snapshot_at", name="uq_roster_snapshot_membership"),)


class TeamGameStats(TimestampedModel):
    __tablename__ = "team_game_stats"
    game_id: Mapped[UUID] = mapped_column(ForeignKey("games.id"))
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"))
    opponent_team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"))
    home_away: Mapped[str] = mapped_column(String(10))
    result: Mapped[str] = mapped_column(String(10))
    minutes: Mapped[str] = mapped_column(String(20))
    points: Mapped[int] = mapped_column(Integer)
    field_goals_made: Mapped[int] = mapped_column(Integer)
    field_goals_attempted: Mapped[int] = mapped_column(Integer)
    three_pointers_made: Mapped[int] = mapped_column(Integer)
    three_pointers_attempted: Mapped[int] = mapped_column(Integer)
    free_throws_made: Mapped[int] = mapped_column(Integer)
    free_throws_attempted: Mapped[int] = mapped_column(Integer)
    offensive_rebounds: Mapped[int] = mapped_column(Integer)
    defensive_rebounds: Mapped[int] = mapped_column(Integer)
    total_rebounds: Mapped[int] = mapped_column(Integer)
    assists: Mapped[int] = mapped_column(Integer)
    steals: Mapped[int] = mapped_column(Integer)
    blocks: Mapped[int] = mapped_column(Integer)
    turnovers: Mapped[int] = mapped_column(Integer)
    personal_fouls: Mapped[int] = mapped_column(Integer)
    plus_minus: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_run_id: Mapped[UUID] = mapped_column(ForeignKey("source_runs.id"))
    __table_args__ = (UniqueConstraint("game_id", "team_id", name="uq_team_game_stats"),)


class PlayerGameStats(TimestampedModel):
    __tablename__ = "player_game_stats"
    game_id: Mapped[UUID] = mapped_column(ForeignKey("games.id"))
    player_id: Mapped[UUID] = mapped_column(ForeignKey("players.id"))
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"))
    starter: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    participation_status: Mapped[str] = mapped_column(String(30))
    status_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    minutes: Mapped[str | None] = mapped_column(String(20), nullable=True)
    points: Mapped[int] = mapped_column(Integer)
    field_goals_made: Mapped[int] = mapped_column(Integer)
    field_goals_attempted: Mapped[int] = mapped_column(Integer)
    three_pointers_made: Mapped[int] = mapped_column(Integer)
    three_pointers_attempted: Mapped[int] = mapped_column(Integer)
    free_throws_made: Mapped[int] = mapped_column(Integer)
    free_throws_attempted: Mapped[int] = mapped_column(Integer)
    offensive_rebounds: Mapped[int] = mapped_column(Integer)
    defensive_rebounds: Mapped[int] = mapped_column(Integer)
    total_rebounds: Mapped[int] = mapped_column(Integer)
    assists: Mapped[int] = mapped_column(Integer)
    steals: Mapped[int] = mapped_column(Integer)
    blocks: Mapped[int] = mapped_column(Integer)
    turnovers: Mapped[int] = mapped_column(Integer)
    personal_fouls: Mapped[int] = mapped_column(Integer)
    plus_minus: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_run_id: Mapped[UUID] = mapped_column(ForeignKey("source_runs.id"))
    __table_args__ = (UniqueConstraint("game_id", "player_id", "team_id", name="uq_player_game_stats"),)


class PlayByPlayEvent(TimestampedModel):
    __tablename__ = "play_by_play_events"
    game_id: Mapped[UUID] = mapped_column(ForeignKey("games.id"))
    provider_name: Mapped[str] = mapped_column(String(100))
    provider_event_id: Mapped[str] = mapped_column(String(150))
    sequence_number: Mapped[int] = mapped_column(Integer)
    period: Mapped[int] = mapped_column(Integer)
    clock_seconds_remaining: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(40))
    outcome: Mapped[str | None] = mapped_column(String(20), nullable=True)
    points_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    home_score: Mapped[int] = mapped_column(Integer)
    away_score: Mapped[int] = mapped_column(Integer)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_run_id: Mapped[UUID] = mapped_column(ForeignKey("source_runs.id"))
    __table_args__ = (
        UniqueConstraint("game_id", "provider_name", "provider_event_id", name="uq_play_event_provider_identity"),
        UniqueConstraint("game_id", "provider_name", "sequence_number", name="uq_play_event_provider_sequence"),
        CheckConstraint("sequence_number >= 0", name="ck_play_event_sequence_nonnegative"),
        CheckConstraint("period > 0", name="ck_play_event_period_positive"),
        CheckConstraint("clock_seconds_remaining >= 0 AND clock_seconds_remaining <= 720", name="ck_play_event_clock_range"),
        CheckConstraint("home_score >= 0 AND away_score >= 0", name="ck_play_event_scores_nonnegative"),
    )


class PlayByPlayEventParticipant(TimestampedModel):
    __tablename__ = "play_by_play_event_participants"
    event_id: Mapped[UUID] = mapped_column(ForeignKey("play_by_play_events.id"))
    role: Mapped[str] = mapped_column(String(40))
    team_id: Mapped[UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    player_id: Mapped[UUID | None] = mapped_column(ForeignKey("players.id"), nullable=True)
    __table_args__ = (
        UniqueConstraint("event_id", "role", name="uq_play_event_participant_role"),
        CheckConstraint("(team_id IS NOT NULL AND player_id IS NULL) OR (team_id IS NULL AND player_id IS NOT NULL)", name="ck_play_event_one_participant_identity"),
    )


class Shot(TimestampedModel):
    __tablename__ = "shots"
    game_id: Mapped[UUID] = mapped_column(ForeignKey("games.id"))
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"))
    player_id: Mapped[UUID] = mapped_column(ForeignKey("players.id"))
    provider_name: Mapped[str] = mapped_column(String(100))
    provider_shot_id: Mapped[str] = mapped_column(String(150))
    period: Mapped[int] = mapped_column(Integer)
    clock: Mapped[str] = mapped_column(String(20))
    sequence_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider_x: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    provider_y: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    normalized_x: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    normalized_y: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    shot_distance: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)
    zone_version: Mapped[str] = mapped_column(String(50))
    zone_code: Mapped[str] = mapped_column(String(50))
    shot_type: Mapped[str] = mapped_column(String(30))
    result: Mapped[str] = mapped_column(String(20))
    point_value: Mapped[int] = mapped_column(Integer)
    source_run_id: Mapped[UUID] = mapped_column(ForeignKey("source_runs.id"))
    __table_args__ = (
        UniqueConstraint("provider_name", "game_id", "provider_shot_id", name="uq_shot_provider_identity"),
        Index("ix_shots_game_sequence", "game_id", "sequence_number"),
        Index("ix_shots_player_game", "player_id", "game_id"),
        Index("ix_shots_team_game", "team_id", "game_id"),
        Index("ix_shots_zone", "zone_version", "zone_code"),
        CheckConstraint("period > 0", name="ck_shots_period_positive"),
        CheckConstraint("sequence_number IS NULL OR sequence_number >= 0", name="ck_shots_sequence_nonnegative"),
        CheckConstraint("shot_distance IS NULL OR shot_distance >= 0", name="ck_shots_distance_nonnegative"),
        CheckConstraint("provider_x IS NULL OR provider_y IS NOT NULL", name="ck_shots_provider_coordinates_pair"),
        CheckConstraint("provider_y IS NULL OR provider_x IS NOT NULL", name="ck_shots_provider_coordinates_pair_y"),
        CheckConstraint("normalized_x IS NULL OR normalized_y IS NOT NULL", name="ck_shots_normalized_coordinates_pair"),
        CheckConstraint("normalized_y IS NULL OR normalized_x IS NOT NULL", name="ck_shots_normalized_coordinates_pair_y"),
        CheckConstraint("point_value IN (0, 1, 2, 3)", name="ck_shots_point_value"),
    )


class StandingsSnapshot(TimestampedModel):
    __tablename__ = "standings_snapshots"
    season_id: Mapped[UUID] = mapped_column(ForeignKey("seasons.id"))
    competition_id: Mapped[UUID] = mapped_column(ForeignKey("competitions.id"))
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    wins: Mapped[int] = mapped_column(Integer)
    losses: Mapped[int] = mapped_column(Integer)
    win_percentage: Mapped[float | None] = mapped_column(Numeric(6, 5), nullable=True)
    conference_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    league_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    games_behind: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    home_wins: Mapped[int | None] = mapped_column(Integer, nullable=True)
    home_losses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_wins: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_losses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_ten_wins: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_ten_losses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    streak_text: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_run_id: Mapped[UUID] = mapped_column(ForeignKey("source_runs.id"))
    __table_args__ = (UniqueConstraint("season_id", "competition_id", "team_id", "observed_at", name="uq_standings_snapshot"),)


class CoverageEvaluation(TimestampedModel):
    __tablename__ = "coverage_evaluations"
    dataset_name: Mapped[str] = mapped_column(String(100))
    dataset_release_id: Mapped[UUID | None] = mapped_column(ForeignKey("dataset_releases.id"), nullable=True)
    league_id: Mapped[UUID | None] = mapped_column(ForeignKey("leagues.id"), nullable=True)
    season_id: Mapped[UUID | None] = mapped_column(ForeignKey("seasons.id"), nullable=True)
    competition_id: Mapped[UUID | None] = mapped_column(ForeignKey("competitions.id"), nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    included_games: Mapped[int] = mapped_column(Integer)
    expected_games: Mapped[int | None] = mapped_column(Integer, nullable=True)
    included_entities: Mapped[int] = mapped_column(Integer)
    expected_entities: Mapped[int | None] = mapped_column(Integer, nullable=True)
    coverage_ratio: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    completeness_status: Mapped[str] = mapped_column(String(30))
    publication_status: Mapped[str] = mapped_column(String(30))
    blocking_reasons: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    policy_version: Mapped[str] = mapped_column(String(50))
