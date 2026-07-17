from __future__ import annotations

import argparse
import json
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.providers.registry import create_teams_provider
from backend.app.services.players import ingest_players_reference
from backend.app.services.rosters import ingest_rosters_reference


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest provider-neutral fixture players and rosters.")
    parser.add_argument("--provider", default="fixture")
    parser.add_argument("--revision", default="v1", choices=("v1", "v2"))
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    provider = create_teams_provider(args.provider)
    players, player_schema, player_fingerprint, player_revision = provider.load_players(args.revision)
    rosters, roster_schema, roster_fingerprint, roster_revision = provider.load_rosters(args.revision)
    if not provider.synthetic:
        raise SystemExit("Phase 3B only permits the fixture provider.")
    if args.validate_only:
        result = {
            "provider": provider.name,
            "revision": args.revision,
            "players": {"records": len(players), "schema_version": player_schema, "fingerprint": player_fingerprint, "revision": player_revision},
            "rosters": {"records": len(rosters), "schema_version": roster_schema, "fingerprint": roster_fingerprint, "revision": roster_revision},
            "publication_status": "withheld",
            "synthetic": provider.synthetic,
        }
    else:
        database_url = os.getenv("NBA_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not database_url or not database_url.startswith("postgres"):
            raise SystemExit("PostgreSQL DATABASE_URL is required for persistence ingestion.")
        engine = create_engine(database_url, pool_pre_ping=True)
        with Session(engine) as session:
            with session.begin():
                player_result = ingest_players_reference(session, provider=provider.name, players=players, schema_version=player_schema, normalized_payload_fingerprint=player_fingerprint, synthetic=provider.synthetic)
                roster_result = ingest_rosters_reference(session, provider=provider.name, rosters=rosters, schema_version=roster_schema, normalized_payload_fingerprint=roster_fingerprint, synthetic=provider.synthetic)
        engine.dispose()
        result = {"provider": provider.name, "revision": args.revision, "players": player_result, "rosters": roster_result, "publication_status": "withheld", "synthetic": provider.synthetic}
    print(json.dumps(result, sort_keys=True) if args.json_output else f"Players: {result['players']}; rosters: {result['rosters']}; publication withheld.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
