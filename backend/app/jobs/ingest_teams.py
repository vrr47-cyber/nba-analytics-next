from __future__ import annotations

import argparse
import json
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.domain.team_scope import ACTIVE_TEAMS_FIXTURE_POLICY
from backend.app.providers.registry import create_teams_provider
from backend.app.services.teams import ingest_teams_reference


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest the provider-neutral teams dataset.")
    parser.add_argument("--provider", default="fixture")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    provider = create_teams_provider(args.provider)
    league, teams, schema_version, fingerprint, scope = provider.load_teams(ACTIVE_TEAMS_FIXTURE_POLICY)
    if not provider.synthetic and os.getenv("NBA_ENVIRONMENT") == "production":
        raise SystemExit("Phase 3A only permits the fixture provider.")
    if args.validate_only:
        result = {"provider": provider.name, "dataset": "teams", "records": len(teams), "schema_version": schema_version, "normalized_payload_fingerprint": fingerprint, "scope_policy": scope.policy_version, "synthetic": provider.synthetic, "publication_status": "withheld"}
    else:
        database_url = os.getenv("NBA_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not database_url or not database_url.startswith("postgres"):
            raise SystemExit("PostgreSQL DATABASE_URL is required for persistence ingestion.")
        engine = create_engine(database_url, pool_pre_ping=True)
        with Session(engine) as session:
            with session.begin():
                result = ingest_teams_reference(session, provider=provider.name, league=league, teams=teams, schema_version=schema_version, normalized_payload_fingerprint=fingerprint, scope_policy=scope, synthetic=provider.synthetic)
        engine.dispose()
    print(json.dumps(result, sort_keys=True) if args.json_output else f"Teams {result['coverage_status'] if 'coverage_status' in result else 'validated'}; publication {result['publication_status']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
