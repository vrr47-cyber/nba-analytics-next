from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from backend.app.services.bundle import BundleError, validate_bundle


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
        summary = {"valid": True, "dataset": bundle.manifest.dataset_name, "version": bundle.manifest.dataset_version, "synthetic": bundle.manifest.synthetic, "files": len(bundle.manifest.files), "rows": sum(len(rows) for rows in bundle.records.values()), "validate_only": args.validate_only, "correction_mode": args.correction_mode, "warnings": bundle.warnings}
        print(json.dumps(summary) if args.json_output else f"Validated {summary['rows']} rows across {summary['files']} files for {summary['dataset']} {summary['version']}.")
        return 0
    except BundleError as exc:
        print(json.dumps({"valid": False, "error": str(exc)}) if args.json_output else f"Bundle rejected: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
