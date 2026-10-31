#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 tools/compiler.py
echo "[BUILD OK] Synced to BetterHud_Pack.zip"
