#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "=============================================="
echo " hunter3eye"
echo "=============================================="
if ! command -v python3 >/dev/null 2>&1; then
    echo "[!] python3 not found."
    exit 1
fi
python3 run.py
