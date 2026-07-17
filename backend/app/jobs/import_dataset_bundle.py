from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.services.bundle import BundleError, import_validated_bundle, validate_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and import a provider-neutral dataset bundle.")
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--correction-mode", action="store_true")
    parser.add_argument("--allow-synthetic", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    try:
        bundle = validate_bundle(args.bundle)
        if bundle.manifest.synthetic and (not args.allow_synthetic or os.getenv("NBA_ENVIRONMENT") == "production"):
            raise BundleError("synthetic bundles require --allow-synthetic and are forbidden in production")
        if args.validate_only:
            summary = {"valid": True, "dataset": bundle.manifest.dataset_name, "version": bundle.manifest.dataset_version, "synthetic": bundle.manifest.synthetic, "files": len(bundle.manifest.files), "rows": sum(len(rows) for rows in bundle.records.values()), "validate_only": True, "correction_mode": args.correction_mode, "warnings": bundle.warnings}
        else:
            database_url = os.getenv("NBA_DATABASE_URL") or os.getenv("DATABASE_URL")
            if not database_url or not database_url.startswith("postgres"):
                raise BundleError("PostgreSQL DATABASE_URL is required for persistence import")
            engine = create_engine(database_url, pool_pre_ping=True)
            with Session(engine) as session:
                with session.begin():
                    summary = {"valid": True, "validate_only": False, "correction_mode": args.correction_mode, "warnings": bundle.warnings, **import_validated_bundle(bundle, session, correction_mode=args.correction_mode)}
            engine.dispose()
        if args.json_output:
            print(json.dumps(summary))
        else:
            action = "Validated" if args.validate_only else "Imported"
            print(f"{action} {summary['rows']} rows for {summary['dataset']} {summary['version']}.")
        return 0
    except BundleError as exc:
        print(json.dumps({"valid": False, "error": str(exc)}) if args.json_output else f"Bundle rejected: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
