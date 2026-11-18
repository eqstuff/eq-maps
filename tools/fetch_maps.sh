#!/usr/bin/env bash
# Fetch Good's maps (Goodurden, via RedGuides) into data/goodurden-maps (gitignored).
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -d data/goodurden-maps/.git ]; then
  git -C data/goodurden-maps pull --ff-only
else
  mkdir -p data
  GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/RedGuides/goodurden-maps data/goodurden-maps
fi
git -C data/goodurden-maps rev-parse --short HEAD
