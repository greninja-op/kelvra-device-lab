#!/usr/bin/env bash
# =========================================================================
# KELVRA Device Lab — Standalone Server POSIX Launcher
# Dedicated Port: 8098
# =========================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

echo "[KELVRA Device Lab] Initializing standalone service on port 8098..."
exec python3 run_standalone.py
