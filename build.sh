#!/usr/bin/env bash
# Build the interactive guide and the route cheat sheet for one zone.
#   ./build.sh arxmentis            # uses data/brewall-maps (run tools/fetch_maps.sh first)
#   MAP_DIR=/path/to/maps ./build.sh arxmentis
set -euo pipefail
cd "$(dirname "$0")"
ZONE="${1:?usage: ./build.sh <zone>   (a module in tools/zones/)}"
DEFAULT_MAP="data/brewall-maps/Brewall's Maps"
MAP_DIR="${MAP_DIR:-$DEFAULT_MAP}"
OUT="site/$ZONE"
mkdir -p "$OUT"
python3 -I tools/build_guide.py "$ZONE" "$MAP_DIR" "$OUT"          # index.html + routes.json
python3 -I tools/build_routes_page.py "$ZONE" "$MAP_DIR" "$OUT"    # cheatsheet.html
echo "built $OUT"
