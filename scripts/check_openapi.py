import json
from pathlib import Path

document = json.loads(Path("backend/openapi.json").read_text())
paths = set(document.get("paths", {}))
required = {"/health/live", "/health/ready", "/api/v1/status", "/api/v1/meta/seasons"}
missing = required - paths
if missing:
    raise SystemExit(f"OpenAPI is missing required paths: {sorted(missing)}")
print("OpenAPI contract check passed.")
