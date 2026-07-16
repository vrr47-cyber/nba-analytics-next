#!/usr/bin/env bash
set -euo pipefail
echo "WARNING: this removes the local PostgreSQL volume and all local data."
read -r -p "Type RESET to continue: " confirmation
[[ "$confirmation" == "RESET" ]] || { echo "Cancelled."; exit 1; }
docker compose -f infra/docker/docker-compose.yml down -v
