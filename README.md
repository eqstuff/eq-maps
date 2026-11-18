# eq-maps

**Live site:** https://eqstuff.github.io/eq-maps/ · **License:** [0BSD](LICENSE) (use it however you like)

Turn the flat line-drawing maps of complicated, multi-level EverQuest zones into something you can actually navigate: a floor-by-floor breakdown, a diagram of which floors connect to which, and turn-by-turn directions between named rooms with the compass direction to head out of each one.

The first zone done is **Arx Mentis** (13 floor heights, 23 staircases/ramps, 21 named rooms/waypoints). The tooling is generic; each zone is one small config file.

| Page | What it does |
|---|---|
| `site/arxmentis/index.html` | Interactive connection diagram with a small outline of each floor. Click a floor or room for the start, another for the destination: the stairs (and teleport) between them light up, everything else fades, and the steps appear with exit headings and click-to-copy `/way` waypoints. Plus a plan view of every floor. |
| `site/arxmentis/cheatsheet.html` | Route finder, 19×19 matrix and per-room cheat sheets: “from X to Y: leave heading E, take S8 up…”. |

## Quick start

```bash
pip install -r tools/requirements.txt
tools/fetch_maps.sh                 # clones Good's maps into data/ (gitignored)
./build.sh arxmentis                # writes site/arxmentis/{index.html,routes.json,cheatsheet.html}
python3 -m http.server -d site 8000 # open http://localhost:8000/
```

`index.html` loads `routes.json` with `fetch()`, so view it through a web server (GitHub Pages, or the one-liner above), not by double-clicking the file.

## Publishing

`.github/workflows/pages.yml` deploys `site/` to GitHub Pages on every push to `main`. In the repo settings choose **Pages → Source: GitHub Actions**. The built pages are committed under `site/`, so a push is all it takes; rebuild first if you changed anything in `tools/`.

## Layout

```
build.sh                    one command: build every page for a zone
tools/
  config.py                 loads tools/zones/<zone>.py (selected by $EQ_ZONE)
  zones/arxmentis.py        ALL zone-specific knowledge: floor heights, names, which labels are rooms, notes
  model.py                  parse map file -> floors, stairs (clustering), labels
  route.py                  walkable grids per floor, pathfinding, route graph
  build_guide.py            interactive diagram + floor plans + routes.json
  build_routes_page.py      matrix / cheat-sheet page
  analyze_levels.py         step 1 for a new zone: find floor heights, stairs, labels
  debug_grids.py            picture of the computed walkable areas (for when a room is unreachable)
  fetch_maps.sh             get the source maps
docs/
  DESIGN.md                 the idea, goals, architecture, algorithms, decisions
  MAP_FORMAT.md             Map file format (Good's and Brewall's) and coordinate conventions
  ADAPTING.md               checklist for mapping another zone
  LESSONS.md                what went wrong while building it, and the fixes
site/                       built output (what GitHub Pages serves)
CLAUDE.md                   orientation notes for AI-assisted sessions
```

## Adding another zone

Each zone is one config file plus a build. Start with [docs/ADAPTING.md](docs/ADAPTING.md); [docs/DESIGN.md](docs/DESIGN.md) explains how it all works and [docs/LESSONS.md](docs/LESSONS.md) lists the traps already hit.

## License

The code, docs and generated pages in this repository are released under the [BSD Zero Clause License](LICENSE): copy, modify and redistribute freely, with no attribution required. The license covers what is written here; the underlying map data is Brewall's work (below) and isn't redistributed in this repo, although the generated pages contain information derived from it.

## Credits and caveats

Map data is from [Good's maps](https://github.com/RedGuides/goodurden-maps) (Goodurden, via RedGuides); it is not redistributed here. This is an unofficial derived guide. Compass headings and `/loc` values are computed from the map file and have **not** been verified in the game client; see `docs/MAP_FORMAT.md` and spot-check one stair with `/loc` before trusting them. EverQuest is a trademark of its owners; this project is not affiliated with them.
