# Design

## The problem

Arx Mentis is a tall, many-floored tower zone. Brewall's map draws it as one flat pile of coloured line segments, and floors overlap when viewed from above, so it's hard to answer simple questions:

* Which floors exist, and what's on each?
* What connects to what? Which stairs do I take to get from the Relic Keep to the Observation Deck?
* From room A, which way do I walk out of the room to reach room B?

## Goals (as originally requested, in order)

1. Take the Brewall maps pack, decipher the Arx Mentis map and produce **a breakdown of the floors and what connects to where**, in a form a person can understand.
2. Treat the **named rooms as destinations and waypoints** and generate a matrix / cheat sheet for getting from any room to any other, **saying which direction to head out of the room** when leaving.
3. Make the connection diagram **interactive**: click one box as source and another as destination (swappable); highlight the stairs between them, grey out the rest; show **which direction to exit each location toward the next**.
4. **Publish** it so friends can use it (GitHub Pages), and keep enough documentation to fix bugs or do the same for other complex zones.

Non-goals: perfect in-game accuracy (the map file has no doors/zone lines), real-time position tracking, 3D rendering.

## Pipeline

```
Brewall .txt files
   |  tools/model.py
   v
floors (by Z) + stairs (clustered sloped segments) + labels
   |  tools/route.py
   v
per-floor walkable grid -> pathfinding between rooms and stair ends -> route graph
   |  tools/build_guide.py / build_routes_page.py
   v
index.html + routes.json (interactive guide), cheatsheet.html (matrix)
```

All zone-specific knowledge (floor heights, names, which labels are rooms, notes) is in `tools/zones/<zone>.py`; the three stages are generic.

### Stage 1: floors, stairs, labels (`model.py`)

* **Floors.** Walls of one floor share (nearly) the same Z. Histogramming Z of flat segments (`analyze_levels.py`) shows clear peaks. The peaks are typed into the zone config as `LEVELS`; any segment or stair end is assigned to the nearest level within 4.5 units (`lvl()`), labels within 12 (they float above the floor). Small peaks (stair landings, annexes) are kept as levels too, drawn as dashed "minor" boxes.
* **Stairs.** Sloped segments are the stair rails and rungs. Segments whose endpoints touch (< 4 units in 3-D) are joined with union-find into *clusters*. A cluster whose lowest and highest ends map to two different levels is a **stair**; anything else is *terrain* (cave slopes) and is only drawn.
* **Rails to stairs.** The two rails of one flight are separate clusters, so clusters with the same (lower, upper) level whose bounding boxes are within 20 units are merged into one stair (`MERGE_GAP` per zone allows more, e.g. the pit's four ramps meeting at the teleport cross use 80). Stairs are numbered S1… sorted by (lower level, upper level, x).
* **Feet and heads.** For each stair, the endpoints at its lowest/highest Z (±1.5) are clustered (radius 25) into one or more **feet** and **heads**. A fork, like S5 (one top, two flights down), has two feet and one head. Never average them: the average of two feet lies in empty space.

### Stage 2: walkable areas and routes (`route.py`)

Rooms are *labels*, not polygons, so a route needs a notion of "walkable". For each floor a 1-unit grid is built:

1. **Walls**: flat segments rasterised, dilated 3×3 so diagonal gaps can't leak.
2. **Inside vs outside**: walls plus the stair rails/rungs (as barriers) are dilated by 2 more cells; regions of free cells that touch the grid border are *outside*. Everything else is inside. (A point-in-polygon even-odd test was tried first and failed: outlines aren't closed polygons. See LESSONS.)
3. **Stairs** are forced walkable: the strip between straight rails, or cells along the rails for bent flights.
4. **Open levels** (caves with unclosed outlines) skip the inside test: only walls block.
5. **Sealed rooms**: a room whose label lies in a tiny (< 1500 cell) enclosed region (a closed chamber with no drawn door) is snapped to the nearest cell of the largest region, i.e. you're routed to its walls.

Nodes are every room and every stair end. For each node, `skimage.graph.MCP_Geometric` computes shortest paths on its floor's grid to every other node on that floor. A path is simplified (Douglas–Peucker, tolerance 7), turned into **compass legs** (8 directions; legs shorter than 14 units dropped; lengths rounded to 10), and stored.

The **route graph** (networkx) joins nodes on the same floor with the grid distance (+1) and the two ends of a stair with its length (Manhattan foot→head plus the height change). A route is a shortest path in that graph; consecutive same-floor nodes are walks (with legs), stair edges are "up/down". The first leg's heading is the "leave the room heading X" answer.

For the interactive guide, endpoints can be a whole *floor* instead of a room: a temporary virtual node connected to every node on that floor is added for the query, so "anywhere on +172" works. Virtual endpoints have no walk legs, which is why a floor-only start gets no first exit heading.

### Stage 3: pages

**Floor plans** are inline SVG, one per floor, drawn straight from the segments (north up, east right; see MAP_FORMAT).

**Connection diagram** (`build_guide.py`):

* One box per floor, stacked by height, listing its rooms as clickable chips.
* Each stair is an "edge" drawn in a right-hand gutter: out of the upper floor's box, along a vertical **lane**, back into the lower floor's box. Lanes are assigned greedily (interval colouring) so edges that overlap vertically get different lanes; the stair number sits on the lane. Entry points on a box are spread evenly down its right side.
* `routes.json` (about 860 KB) holds a precomputed route for every ordered pair of endpoints (floors and rooms): `{"F-1|R3": {"h": "<ol>…", "s": [{"id","dir","fr","to","exit"}], "f": [floors visited]}}`. It's a separate file (fetched with a relative URL) to keep the HTML small and editable.
* The inline script keeps `{A, B}` state: click picks A, then B, a third click restarts (`pick()`); selects mirror it; Swap and Clear buttons. `render()` adds CSS classes: `.diag.active` greys every `.edge`/`.bx` and `.on` restores the path's; `.src`/`.dst` outline the endpoints; "leave ↗ NE" pills are SVG groups positioned using the box anchor coordinates exported from Python (`ANCH`, `BOX`).

**Cheat sheet** (`build_routes_page.py`): a self-contained page (about 400 KB) with a route finder, a rooms × rooms matrix (cell = exit heading + stairs up/down, colour = distance) and collapsible per-room lists.

## Why these choices

* **Static pages + precomputed routes**: hostable on GitHub Pages with no backend; the heavy geometry runs offline in Python.
* **Config per zone, generic tools**: the only judgement calls (what the floors are called, what counts as a room) are in one file.
* **Compass headings from real paths** rather than straight lines between rooms, because corridors and walls decide which exit you take.
* **Keep the original coordinates visible** (`/loc` conversion) so the output can be checked in game.

## Known limitations

* Doors are unknown; every wall gap is treated as a doorway.
* Rooms are label points. A route ends at the label, not "at the door".
* Cave levels are approximate; sealed chambers route to their outside walls.
* Teleports, zone lines and the unconnected sky platform aren't modelled.
* Compass/`/loc` orientation is derived, not verified in the client.
* Stair lengths use a Manhattan estimate; distances are ranking aids, not exact.
