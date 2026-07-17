from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class ValidationResult(StrEnum):
    PASSED = "passed"
    PASSED_WITH_WARNINGS = "passed_with_warnings"
    FAILED = "failed"


class ValidationIssue(BaseModel):
    code: str
    severity: str
    entity_type: str
    entity_id: UUID | str | None = None
    message: str
    remediation: str | None = None


class ConsistencyReport(BaseModel):
    result: ValidationResult
    issues: list[ValidationIssue] = Field(default_factory=list)


def validate_bundle_references(records: dict[str, list[dict]]) -> ConsistencyReport:
    issues: list[ValidationIssue] = []
    teams = {row.get("source", {}).get("external_id") for row in records.get("teams", [])}
    players = {row.get("source", {}).get("external_id") for row in records.get("players", [])}
    for row in records.get("rosters", []):
        if row.get("team_external_id") not in teams:
            issues.append(ValidationIssue(code="missing_team_reference", severity="error", entity_type="roster", message="Roster references an unknown provider team."))
        if row.get("player_external_id") not in players:
            issues.append(ValidationIssue(code="missing_player_reference", severity="error", entity_type="roster", message="Roster references an unknown provider player."))
    return ConsistencyReport(result=ValidationResult.FAILED if issues else ValidationResult.PASSED)
