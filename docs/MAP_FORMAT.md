# Brewall map files

A zone's map is a set of plain-text files named after the zone's short name (Arx Mentis: `arxmentis`):

| File | Contents |
|---|---|
| `<zone>.txt` | Geometry: `L` (line) records, the walls/outlines of the zone |
| `<zone>_1.txt` | Layer 1: `P` (point label) records that sit in the zone: room names, NPCs, merchants, spawns |
| `<zone>_2.txt` | Layer 2: the **map key** (legend). In Arx Mentis it is drawn far outside the zone (x up to ~2030, y up to ~2370), so it must be excluded from bounding boxes and plans |

## Records

```
L x1, y1, z1, x2, y2, z2, r, g, b
P x, y, z, r, g, b, size, label text
```

* Fields are comma separated with optional spaces. Labels use `_` for spaces (`Protarx_Infusion_Lab`); the tools replace `_` with a space.
* Label prefixes seen in Arx Mentis: `GS:` ground spawn, `(Hunter)` Hunter-achievement mobs, `(Quests...)` quest NPCs, `to #N` markers (the mapper's own numbered exits). Which prefixes count as "rooms" is set per zone in `is_room_label()`.
* A segment is **flat** if z1 ≈ z2 (a wall outline at one height) and **sloped** otherwise (a stair rail/rung or terrain edge). 1688 segments in Arx Mentis: 1200 flat, 488 sloped.

## Coordinates

Map coordinates are the in-game world coordinates, negated and with the axes swapped relative to what `/loc` prints:

```
/loc prints "Y, X, Z"
map x = -X   (second /loc number)
map y = -Y   (first /loc number)
map z =  Z
```

so a map point (x, y, z) corresponds to `/loc` = (−y, −x, z). The conversion follows the community-documented format (e.g. the Allakhazam EverQuest forum thread on map file coordinates). With north at the top of the in-game map this puts **north at −y (page up) and east at +x (page right)** when drawn with y increasing downward, which is how the generated plans are drawn and how compass headings are computed (`hd()` in `route.py`).

## Waypoints (`/way`)

The generated pages print locations as `/way Y, X, Z` commands (for example `/way -20, 2, -1`). `/way` (short for `/waypoint`) takes the same Y, X, Z order that `/loc` prints, so a map point (x, y) on a floor at height z becomes `/way −y, −x, z`. Pages render these as click-to-copy chips: paste into the chat window and EverQuest sets a waypoint you can follow. The Z used is the floor's nominal height (labels use their own Z).

**Not verified in the client.** Before trusting headings for a new zone, stand at a known stair top, type `/loc`, and compare with the numbers the page prints. If north/south or east/west are mirrored, fix the sign in `hd()` and `loc()`.

## What the file does NOT contain

Doors (a doorway is just a gap in an outline), zone lines, teleport destinations, elevators and any notion of rooms (rooms are only inferred from labels). Anything in the generated pages that says "walk through here" assumes gaps are doorways.
