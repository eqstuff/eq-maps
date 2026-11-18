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

**Teleports.** The map file has no portals, so links the player knows about are declared in the zone config (`PORTALS`: from room, to room, cost) and added to the route graph as extra edges between two room nodes. They appear as a dashed lane with a "T" badge in the diagram, as a "✦ Use the teleport" step in routes, and as a connection in the floor cards. Portals are two-way; a one-way portal isn't supported yet (it would need a directed graph). Arx Mentis has one, T1: the pad at the top of the pit pyramid to the ground-floor central hub, which comes from in-game experience, not from the map.

For the interactive guide, endpoints can be a whole *floor* instead of a room: a temporary virtual node connected to every node on that floor is added for the query, so "anywhere on +172" works. Virtual endpoints have no walk legs, which is why a floor-only start gets no first exit heading.

### Stage 3: pages

**Floor plans** are inline SVG, one per floor, drawn straight from the segments (north up, east right; see MAP_FORMAT).

**Connection diagram** (`build_guide.py`):

* One box per floor, stacked by height, listing its rooms as clickable chips.
* Each stair is an "edge" drawn in a right-hand gutter: out of the upper floor's box, along a vertical **lane**, back into the lower floor's box. Lanes are assigned greedily (interval colouring) so edges that overlap vertically get different lanes; the stair number sits on the lane. Entry points on a box are spread evenly down its right side.
* `routes.json` (about 860 KB) holds a precomputed route for every ordered pair of endpoints (floors and rooms): `{"F-1|R3": {"h": "<ol>…", "s": [{"id","dir","fr","to","exit"}], "f": [floors visited]}}`. It's a separate file (fetched with a relative URL) to keep the HTML small and editable.
* Each floor box carries a **thumbnail**: the floor's wall outline (north up) with a dot per room and a hidden dot per stair end on that floor. Selecting a room turns its dot green (start) or red (destination); stairs on the current route light up orange on both floors they join, and teleport pads turn purple. Clicking a dot selects that room. This makes "where am I on this floor?" a glance.
* Locations are printed as click-to-copy `/way Y, X, Z` chips (`waycmd()`), so players paste them into chat to set a waypoint.
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

## Type-ahead pickers and NPC search

The From/To `<select>`s stay in the page as hidden state holders; `tools/combobox.js` (+ `combobox.css`) layers a type-ahead input on top of each. Entries are floors, rooms, and every non-room point label (NPCs, hunters, ground spawns). Typing filters by accent-insensitive substring over all words; start-of-word matches rank first. Choosing an entry sets the select's value and fires `change`, so the existing render logic is unchanged.

An NPC entry resolves to the room it stands in: `route.label_points()` takes each label's (x, y, floor) and `route.nearest_room()` picks the room with the least *walking* distance on that floor (straight-line fallback). If a floor has no named rooms the entry selects the whole floor. The page shows a note ("X is in Y") above the route. These labels are only as accurate as Brewall's map placement, and mobs that wander or respawn elsewhere will be wrong.

## Source switch: Brewall → Good's

The guide was first built from Brewall's maps and later moved to Good's, because Good's labels zone lines and portals (Brewall's has none). Good's geometry differs enough that the pipeline changed:

* A ramp is one or two long sloped lines (223 sloped segments vs Brewall's 488 rail pairs), ending short of the floor heights. Ends are matched to floors with `STAIR_TOL` and tie-broken by nearest floor geometry.
* Outlines have gaps, so the flood-filled walkable grid fell apart into corridor fragments (many rooms "sealed", floors disconnected). The zone now runs in **straight-line mode**: each hop is a compass heading and distance, with no wall avoidance. The graph only needs to know which places connect; whether a link is stairs or a ramp isn't distinguished in the text.
* All label layers (`_1`, `_2`, `_3`, and `P` lines in the main file) are read.
* Floors moved by a few units (pit -483, cross -430, ground 0, annex -5, vaults -70, gardens -35, sky +470). Floor +179 is a raised platform folded into +172.
* Room set changed: Good's has Medical Chamber, Feeding Chamber, Analysis Room, three generators and a separate study; it has no Observation Deck, no "Crasis Whesar" room, and only one Anetarx Extraction Lab.
* The old Brewall output was not byte-comparable, so `routes.json` was regenerated from scratch.

## Dividing a floor into rooms and corridors (recipe for any floor or zone)

Where a floor holds several rooms joined by corridors (Arx Mentis +80 Anetarx and +172 Penutarx), straight lines between room labels cross walls and say little. The generic tools do nothing zone-specific; a floor is divided entirely by data in `tools/zones/<zone>.py`:

1. **Look.** `python3 -I tools/plot_floor.py <zone> <map dir> <level> out.png [x0 x1 y0 y1]` draws the walls with labels, ramp ends and a 10-unit grid. Read coordinates off the grid.
2. **Pieces.** `CORRIDORS` lists corridor pieces `(name, x, y, level)`, anchors on the centre line. Cut at T-junctions and corners where a heading changes, so a leaving direction is unambiguous, but don't slice further than that.
3. **Graph.** `FLOOR_GRAPHS[level]["edges"]` joins neighbours `(A, B, [via points])` (rooms and pieces). The walk goes through the via points (doors, corners). Ramp ends attach to the nearest piece, or per `attach`. Having a `FLOOR_GRAPHS` entry is what marks a floor as divided.
4. **Features.** `CORRIDOR_GROUPS` maps each piece to a named corridor (the thing the user sees). A corridor with a T, or with several exits, is still one feature as long as its exits point in different compass directions; split it only when two exits would share a heading. A piece grouped under a *room's* name is just part of that room's exit. **A corridor with only two links (one way in, one way out) is not a place**: split it in two (one piece per half) and group each half under the room or corridor it leads to; a pass-through that ends in a ramp joins the room at its other end. The build prints a note for any corridor with two or fewer links.
5. **Boxes.** `ROOM_BOX[room] = (x0, x1, y0, y1)` is the map rectangle the room's thumbnail shows (default: a 120-unit square around its label). Corridor thumbnails are cut automatically around their pieces, with the corridor's centre line drawn in colour. `UNIT_ORDER[level]` orders the boxes top to bottom. The build prints a note for any room without a box or piece without a group.

What the user gets: one box per room and per corridor in "What connects to what", each listing its exits as `heading → neighbour`; routes that read room → corridor → corridor → room, one step per feature (consecutive hops inside one feature merge: `route.chunk_hops`); corridor lines between neighbouring boxes (highlighted on a route); and every named corridor is a place of its own: selectable, searchable, in the cheat sheet, standing at its most central piece (`route.py`, kind `feature`).

The division is a reading of the outlines made with zoomed plots (`/tmp`-style scripts that draw one floor's lines with the label points, ramp ends and a 10-unit grid). Check it the same way after changing it. Other floors still use plain straight lines; to divide one, add its corridors and a `FLOOR_GRAPHS` entry.
