#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This cleanup script targets macOS only." >&2
  exit 1
fi

echo "Cleaning desktop/app/dist"
rm -rf desktop/app/dist

echo "Cleaning desktop/app/node_modules"
rm -rf desktop/app/node_modules

echo "Cleaning desktop/app/resources/backend/lifetrace-api"
rm -rf desktop/resources/backend/lifetrace-api

echo "Cleaning desktop/app/resources/frontend/standalone"
rm -rf desktop/resources/frontend/standalone

echo "Cleaning frontend/.next"
rm -rf frontend/.next

echo "Cleaning lifetrace-api.spec"
rm -f lifetrace-api.spec

echo "Cleanup done."
