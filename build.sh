#!/bin/bash
# Nekonote full build script
# Usage: bash build.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "=== Nekonote Full Build ==="
echo ""

# Step 1: Build Python backend with PyInstaller
echo "--- Step 1: Building backend engine ---"
cd "$SCRIPT_DIR/backend"
pip install pyinstaller 2>/dev/null
python build.py
echo ""

# Step 2: Build Electron frontend + create installer
echo "--- Step 2: Building frontend + installer ---"
cd "$SCRIPT_DIR/frontend"
npm install --include=dev
node node_modules/electron-vite/bin/electron-vite.js build
npx electron-builder --win --config electron-builder.json
echo ""

echo "=== Build complete ==="
echo "Installer: frontend/release/"
