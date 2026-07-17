from __future__ import annotations

import argparse
import json
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.providers.registry import create_teams_provider
from backend.app.services.games import ingest_games_reference, validate_games_reference


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest provider-neutral fixture games.")
    parser.add_argument("--provider", default="fixture")
    parser.add_argument("--revision", default="v1", choices=("v1", "v2"))
    parser.add_argument("--correction-mode", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    provider = create_teams_provider(args.provider)
    games, schema_version, fingerprint, revision = provider.load_games(args.revision)
    if not provider.synthetic:
        raise SystemExit("Phase 4 only permits the fixture provider.")
    database_url = os.getenv("NBA_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not database_url or not database_url.startswith("postgres"):
        raise SystemExit("PostgreSQL DATABASE_URL is required to validate game references or persist ingestion.")
    engine = create_engine(database_url, pool_pre_ping=True)
    with Session(engine) as session:
        if args.validate_only:
            result = validate_games_reference(session, provider=provider.name, games=games, correction_mode=args.correction_mode)
            result = {"provider": provider.name, "revision": revision, "schema_version": schema_version, "normalized_payload_fingerprint": fingerprint, "validation": result, "publication_status": "withheld", "synthetic": provider.synthetic}
        else:
            with session.begin():
                result = ingest_games_reference(session, provider=provider.name, games=games, schema_version=schema_version, normalized_payload_fingerprint=fingerprint, synthetic=provider.synthetic, correction_mode=args.correction_mode)
            result = {"provider": provider.name, "revision": revision, **result}
    engine.dispose()
    print(json.dumps(result, sort_keys=True) if args.json_output else f"Games: {result}; publication withheld.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
