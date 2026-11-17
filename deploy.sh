#!/usr/bin/env bash
# Rebuild the site and publish docs/ to the gh-pages branch (GitHub Pages source).
set -euo pipefail
cd "$(dirname "$0")"
python3 build.py
git add -A && git commit -m "Rebuild site" || true
git push origin main
git branch -D gh-pages 2>/dev/null || true
git subtree split --prefix docs -b gh-pages
git push -f origin gh-pages
echo "Live in about a minute: https://business-analyst-services.github.io/net-watch/"
