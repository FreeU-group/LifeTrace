#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script targets macOS only." >&2
  exit 1
fi

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing dependency: $1" >&2
    exit 1
  }
}

require_cmd uv
require_cmd pnpm
require_cmd npm

BACKEND_DIR="desktop/resources/backend/lifetrace-api"
FRONTEND_DIR="desktop/resources/frontend/standalone"

echo "[1/5] Clean old outputs"
rm -rf "$BACKEND_DIR" "$FRONTEND_DIR" desktop/app/dist

echo "[2/5] Build frontend (Next.js standalone)"
(
  cd frontend
  pnpm install
  pnpm build
)

mkdir -p "$(dirname "$FRONTEND_DIR")"
cp -R frontend/.next/standalone "$FRONTEND_DIR"
cp -R frontend/.next/static "$FRONTEND_DIR/.next/static"
cp -R frontend/public "$FRONTEND_DIR/public"

echo "[3/5] Build backend (PyInstaller onedir)"
uv run --group dev pyinstaller lifetrace/server.py \
  --name lifetrace-api \
  --onedir \
  --paths . \
  --collect-all lifetrace \
  --collect-all chromadb \
  --collect-all posthog \
  --collect-all rapidocr_onnxruntime \
  --hidden-import chromadb.telemetry.product.posthog \
  --add-data lifetrace/config/prompt.yaml:lifetrace/config \
  --noupx \
  --distpath desktop/resources/backend

echo "[4/5] Copy configs/models into backend bundle"
mkdir -p "$BACKEND_DIR/config" "$BACKEND_DIR/models"
cp lifetrace/config/*.yaml "$BACKEND_DIR/config/" || true
if ls lifetrace/models/*.onnx >/dev/null 2>&1; then
  cp lifetrace/models/*.onnx "$BACKEND_DIR/models/"
fi

echo "[5/5] Package Electron app (DMG)"
(
  cd desktop/app
  npm install
  npm run dist -- --mac dmg
)

echo "All done. See desktop/app/dist/ for the DMG."
