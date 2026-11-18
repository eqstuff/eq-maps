# Adding another zone

Any Good's (or Brewall) zone with several levels works the same way. Budget a couple of hours; most of it is checking the result.

1. **Get the maps**: `tools/fetch_maps.sh`. Find `<zone>.txt` and the `<zone>_1.txt`, `_2.txt`... label layers in `data/goodurden-maps/Good's Maps/` (zone short names, e.g. `sebilis`, `kedge`).
2. **Create the config**: `cp tools/zones/arxmentis.py tools/zones/<zone>.py`.
3. **Find the floors**: `python3 -I tools/analyze_levels.py "data/goodurden-maps/Good's Maps" <zone>`.
   * Each big peak in the flat-Z histogram is a floor. Put them in `LEVELS` (nominal Z + short name). Peaks within ~5 units of each other usually belong to the same floor (Arx: −484 and −482).
   * Sloped clusters whose Z range runs from one peak to another are stairs; ones that don't match a level are terrain (caves, ramps inside one floor). If a real stair's end is not on any peak, add a level for its landing.
   * Floors that are really a rough cave need an entry in `flat_level()` to collapse the jittery heights into one level, and in `OPEN_LEVELS`.
4. **Names and order**: fill `FLOOR_NAMES`, `ROUTE_NAMES`, `FLOOR_ORDER` (top to bottom), `MINOR_LEVELS` (landings), `SKY_LEVELS` (geometry nothing connects to).
5. **Rooms**: `is_room_label()` decides which labels are destinations. Print the labels from `analyze_levels.py` and exclude NPCs/merchants/spawns by prefix. Add `EXTRA_ROOMS` for unlabeled hubs you want as waypoints. Duplicate names get a floor suffix automatically.
6. **Stairs that merge wrong**: set `MERGE_GAP[level]` (units) for flights whose rails are far apart or that fan out from a hub; see the pit ramps in `arxmentis.py`.
6b. **Teleports**: if the zone has portals between floors, list them in `PORTALS` (room names must match labels or `EXTRA_ROOMS`). Mark in the page text that they come from play experience, since the map doesn't contain them.
7. **Grid levels**: list the connected floors in `GRID_LEVELS` and the cut-off ones in `EXTRA_GRID_LEVELS`.
8. **Build**: `MAP_DIR=... ./build.sh <zone>`. Read the console output:
   * `far-snap nodes` — a node more than 25 cells from a walkable cell (label outside the walls, or a stair end that doesn't line up).
   * `sealed rooms` — rooms treated as closed chambers.
   * the connected-component listing in `python3 -I tools/route.py <zone> <map_dir>`'s output: every room should be in one big component unless the zone really has separate parts. Unreachable pairs are the number to drive to zero.
9. **Look at the masks**: `python3 -I tools/debug_grids.py <zone> <map_dir> grids.png`. Coloured regions are connected walkable areas. A room in its own colour means a wall gap is closed (dilation too aggressive, or a drawn door) or a stair isn't linked to its corridor.
10. **Write the page text**: `floor_note()`, `intro()`, `LIMITS_NOTE`, `SOURCE_NOTE`, titles. Add the zone to `site/index.html`.
11. **Verify in game** at least one stair's `/loc` and one heading (see MAP_FORMAT).

Tuning knobs, if routes look wrong: grid resolution `RES` and the wall dilation in `route.build_grid`; stair cluster radius (4) and feet/heads radius (25) in `model.py`; leg simplification (tolerance 7, min leg 14) in `route.legs_from`; sealed-room size threshold (1500 cells) in `route.py`.

A different map source (not Good's or Brewall) only needs a new parser in `model.load()`; everything after it works on `L`/`P` lists.

## Extra searchable points (safe points, zone lines)

Good's files have zone-line and portal labels but no safe spot. Add them in `tools/zones/<zone>.py` as `EXTRA_POINTS = [dict(name="Safe point", kind="safe point", way=(Y, X, Z))]` using the numbers `/loc` prints in game; they become searchable and resolve to their room like NPCs do. Don't guess coordinates.

## Rooms, floors and routing choices that differ per map pack

* **Rooms** — Good's has no room layer: rooms, NPCs, mission markers and zone lines are all `P` labels. List the rooms explicitly in `ROOM_LABELS`; everything else becomes a searchable point (`label_kind`, `label_text`).
* **Label heights** — some labels float at the wrong Z (Arx's "Protarx Gardens" is at -3.7 but the floor is -35). `room_level()` overrides per room.
* **Routing** — set `STRAIGHT_ROUTES = True` when outlines have gaps (Good's), otherwise leave it off and the tools flood-fill a walkable grid. Straight mode gives one compass heading and distance per hop and never uses walls.
* **Links** — Good's draws a ramp as one or two long sloped lines that stop short of the floors. `STAIR_TOL` widens the match, and `model._end_level()` picks between close floors by which floor's walls are nearest the ramp end.
