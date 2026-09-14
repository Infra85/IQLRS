#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$(dirname "$(readlink -f "$0")")")"

test -f .env || { echo "Missing .env. Copy .env.example and configure production values." >&2; exit 1; }
grep -q '^ACME_EMAIL=' .env || { echo "Missing ACME_EMAIL in .env." >&2; exit 1; }

git pull --ff-only origin main
docker compose build
docker compose up -d db
docker compose --profile tools run --rm migrate
docker compose up -d backend frontend caddy
docker compose ps
