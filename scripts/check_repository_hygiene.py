import subprocess
from pathlib import Path

tracked = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
tracked_present = [path for path in tracked if Path(path).exists()]
forbidden = ("node_modules/", "dist/", ".env", ".sqlite", ".db", ".duckdb", "__pycache__/", ".pytest_cache/")
bad = [path for path in tracked_present if any(token in path for token in forbidden)]
if bad:
    raise SystemExit(f"Generated or local files are tracked: {bad}")
locks = [path for path in tracked_present if Path(path).name in {"package-lock.json", "yarn.lock", "pnpm-lock.yaml"}]
if "pnpm-lock.yaml" not in locks or "package-lock.json" in locks or "yarn.lock" in locks:
    raise SystemExit(f"Expected one pnpm lockfile, found: {locks}")
print("Repository hygiene check passed.")
