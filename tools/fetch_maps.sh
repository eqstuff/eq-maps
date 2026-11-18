#!/usr/bin/env bash
# Fetch Brewall's maps into data/brewall-maps (gitignored).
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -d data/brewall-maps/.git ]; then
  git -C data/brewall-maps pull --ff-only
else
  mkdir -p data
  git clone --depth 1 https://github.com/RedGuides/brewall-maps data/brewall-maps
fi
git -C data/brewall-maps rev-parse --short HEAD
