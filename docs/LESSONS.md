# Lessons and pitfalls

Things that went wrong while building the Arx Mentis guide, and what fixed them. Read this before debugging.

## Data and decoding

* **The "pack" is a git repo of text files**, not a zip. Clone it (`tools/fetch_maps.sh`).
* **The map key is part of the geometry file set.** `arxmentis_2.txt` draws the legend far outside the zone; including it makes the bounding box huge and adds fake floors at z = 0.
* **Two different "south" rooms at Z ≈ −6 and −1.** A lowered ground annex is its own level connected by short steps; merging it into ground hides a real staircase (S3 from the gardens lands in it).
* **Heights are not perfectly flat.** Cave floors vary by tens of units, so `flat_level()` collapses a band to one level. Without it the cave shatters into many "floors".
* **A stair is not one object.** Rails of the same flight are separate clusters (merge by bounding-box gap) and a fork (S5) has two feet. Averaging the foot of a multi-flight stair produced a point in empty space and made the stair look unreachable.
* **Some labels are the mapper's own markers** (`to #2/#3/#4`), not rooms; excluded by `is_room_label()`.

## Walkable-area computation

* **Even-odd point-in-polygon failed.** The outlines aren't closed polygons (corridors are single lines, doorways are gaps, stairs are drawn separately), so the "inside" came out as nonsense blobs. Replaced by *flood fill from the border*: dilate walls and stair rails, anything reachable from the border is outside.
* **Stair rails must be barriers in the flood fill**, otherwise the open end of a stair corridor lets the "outside" flood the whole interior.
* **Diagonal leaks.** An 8-connected rasterised line still lets a diagonal step through; dilating walls 3×3 fixed it (assumes doorways are wider than ~3 units).
* **Sealed chambers.** The Teritarx Preservation Chamber is a closed outline with no door drawn; its label sits in a 341-cell region cut off from everything. Rooms in tiny enclosed regions are routed to the nearest cell of the main region and the page says to look for the door.
* **The cave has no closed outline**, so its floor is "open" (only walls block). Headings through it are rough.

## Pathfinding output

* Raw grid paths zig-zag along walls. Simplify (tolerance 7), drop legs < 14 units, round to 10, and merge same-heading legs, or every route has a dozen 5-unit legs.
* Floor-only endpoints are virtual graph nodes added per query; they must be removed afterwards or later queries shortcut through them.
* The pit and teleport cross are connected to each other but not to the tower. 76 ordered room pairs are therefore "no walking route"; this is expected, not a bug.

## Front end / hosting

* `routes.json` is large (about 860 KB): keep it a separate file and fetch it relatively. It only works through a web server, not `file://`.
* The diagram's room chips wrap inside a width that leaves the right ~100 px of each box free for the "leave →" pills; if you change `boxw`/`CHIPR`, keep that gap.
* GitHub Pages serves `site/`. Commit the built output; the Actions workflow only uploads it.

## Process mistakes worth avoiding

* A module-level variable named `P` (labels) was overwritten by a loop variable in `model.py`: name loop temporaries distinctly.
* Run Python with `-I` (isolated) when reading downloaded data, and keep scripts out of the data directory.
* Verify against a baseline after refactors: building again must give a byte-identical `routes.json` (it did when the tools were moved to the zone-config layout).

## Later additions

* A helper named `way()` clashed with a loop variable `way="up"` in `build_guide.py` ("'str' object is not callable"). The helper is now `waycmd()`; avoid generic names in the big top-level build scripts.
* Adding the T1 portal connected the pit and teleport cross to the tower: 240 new route pairs, and no existing route changed (checked by comparing the `s`/`f` fields of every key in `routes.json` before and after).
* The diagram's room chips, thumbnails and "leave" pills all share the box width: thumbnails take the left ~100 px, the "leave" pills the right ~100 px, chips wrap in between.
