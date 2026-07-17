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
    game_date: Mapped[datetime] = mapped_column(Date)
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
