#!/usr/bin/env bash
set -euo pipefail
rm -rf dist
mkdir -p dist

# Copy public site files into dist/ (no rsync required).
find . -mindepth 1 -maxdepth 1 ! -name dist ! -name .git ! -name .github ! -name node_modules ! -name scripts ! -name .env ! -name .cursor -print0 |
  while IFS= read -r -d '' item; do
    base=$(basename "$item")
    case "$base" in
      server.js|server.py|package.json|package-lock.json|render.yaml|Dockerfile|Procfile|requirements.txt|runtime.txt|.python-version|.dockerignore) continue ;;
    esac
    cp -a "$item" "dist/$base"
  done

# Drop backend/admin-ish files from the static bundle if copied.
rm -f dist/server.js dist/server.py dist/package.json dist/package-lock.json dist/render.yaml 2>/dev/null || true
rm -rf dist/node_modules dist/api/data 2>/dev/null || true

if [[ -f dist/assets/cdn/logo.jpg && ! -f dist/assets/fitness-gurukul-logo.jpg ]]; then
  cp dist/assets/cdn/logo.jpg dist/assets/fitness-gurukul-logo.jpg
fi

echo "Static dist ready ($(find dist -type f | wc -l) files)"
