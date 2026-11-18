"""Zone configuration for Arx Mentis (map: Brewall's maps, files arxmentis.txt / _1 / _2).

Everything zone-specific lives here; the tools in tools/ are generic.  To map another
zone, copy this file to tools/zones/<zone>.py and edit it (see docs/ADAPTING.md).
"""
FILE_PREFIX = "arxmentis"          # arxmentis.txt (geometry), arxmentis_1.txt (labels)
TITLE = "Arx Mentis: floors and connections"

# --- floors -----------------------------------------------------------------
# (nominal map Z, short name).  Found by histogramming the Z of flat wall segments
# (see docs/DESIGN.md).  A segment/stair end belongs to the nearest level within 4.5 units.
LEVELS = [(-484, "Pit floor"), (-429, "Teleport cross"), (-71, "Lower vaults"),
          (-36, "Garden level"), (-6, "Ground south annex"), (-1, "Ground"),
          (24, "Relic Keep"), (45, "East landing"), (80, "Study level"),
          (85, "Landing +85"), (105, "Landing +105"), (115, "Magicae cave"),
          (172, "Upper level"), (468, "Sky platform")]
# Display names for the floor boxes and cards.
FLOOR_NAMES = {468: "Unlabeled sky platform", 172: "Penutarx: upper labs",
               115: "Anetarx: Magicae Sanctuary (cave)", 105: "West corridor landing (+105)",
               85: "West corridor (+85)", 80: "Anetarx: study level", 45: "East landing",
               24: "Protarx: Relic Keep", -1: "Ground: central hub", -6: "Ground south annex",
               -36: "Protarx: gardens & library", -71: "Teritarx: preservation vaults",
               -429: "Teleport cross", -484: "Pit: merchants & quest hall"}
ROUTE_NAMES = {172: "Upper labs", 115: "Magicae cave", 105: "West corridor (+105)",
               85: "West corridor (+85)", 80: "Study level", 45: "East landing",
               24: "Relic Keep level", -1: "Ground", -6: "Ground south annex",
               -36: "Gardens level", -71: "Preservation vaults", -429: "Teleport cross",
               -484: "Pit"}
FLOOR_ORDER = [468, 172, 115, 105, 85, 80, 45, 24, -1, -6, -36, -71, -429, -484]  # top to bottom
MINOR_LEVELS = (105, 85, -6, 468)   # drawn with dashed boxes (landings / annexes)
SKY_LEVELS = (468,)                 # geometry nothing connects to: not selectable in the UI

# --- stairs -----------------------------------------------------------------
# Rails of one stair that start within this many units are merged into one stair.
# The pit's four ramps meet at the teleport cross, so they need a wider gap.
MERGE_GAP = {-484: 80}

# --- cave / irregular floors ------------------------------------------------
# A natural cave has an unclosed outline, so "inside the walls" can't be computed;
# those levels are treated as fully open (rooms there get rougher directions).
OPEN_LEVELS = (115,)
CAVE_LEVEL = 115                    # level whose sloped terrain edges are drawn in plans
CAVE_MIN_Z = 105                    # terrain slopes above this Z belong to the cave

def flat_level(z, lvl):
    """Level for a flat segment at height z.  `lvl(z)` is the nearest-level helper."""
    if 108 <= z <= 135:             # irregular cave floor heights all collapse to +115
        return 115
    if 90 <= z < 108 and lvl(z) is None:
        return 115
    return lvl(z)

def label_level(z, lvl):
    """Level for a P (label) record at height z; labels float above/below floors."""
    if 108 <= z <= 135:
        return 115
    return lvl(z, 12)

# --- rooms (named destinations) ----------------------------------------------
def is_room_label(t):
    """Which P labels count as 'rooms'.  Skip map-key tags, ground spawns, hunters, quest
    NPCs and merchants; what remains are the named areas."""
    if t.startswith(('to #', 'GS:')):
        return False
    if '(Hunter' in t or '(Quest' in t:
        return False
    if t.startswith(('Merchant', 'Tuhita', 'Pelitoi', 'Artun', 'Leko', 'Indri')):
        return False
    return True

# Rooms that have no label in the map but are useful waypoints: (name, x, y, level)
EXTRA_ROOMS = [("Central hub (ground)", 0, 0, -1),
               ("Pit (merchants / Firiona Vie)", 0, -20, -484)]

# --- walkable grids ---------------------------------------------------------
GRID_LEVELS = [172, 115, 105, 85, 80, 45, 24, -1, -6, -36, -71]   # the connected tower
EXTRA_GRID_LEVELS = [-429, -484]                                    # cut off from the tower

# --- page text --------------------------------------------------------------
def floor_note(lv):
    notes = {
        -1: '<p class="note">The three <b>“to #2 / #3 / #4”</b> tags are the mapper’s own markers around the central hub. They sit at the exits that lead to S4/S5 (down to the gardens), S9/S5 (east) and S8 (up to the Relic Keep); the numbering itself isn’t explained in the file, so treat that mapping as a reading.</p>',
        115: '<p class="note">This is a natural cave, so it has irregular sloped edges instead of clean stairs. Part of the west edge climbs to about +160 with no landing drawn.</p>',
        468: '<p class="note">275 line segments in a square hall with round pillars, about 470 units above the ground floor. No stairs, ramps or labels reach it, so the file doesn’t say how you get there (probably a teleport destination, or a scenery shell).</p>',
        -429: '<p class="note">Just a cross-shaped platform with the “Teleport” label. The four long ramps lead down to the pit floor. Where the teleport sends you isn’t in the map data.</p>',
    }
    return notes.get(lv, "")

def intro(n_stairs):
    return ("Decoded from Brewall’s map files (<code>arxmentis.txt</code>, <code>_1</code>, <code>_2</code>). "
            "The zone has 13 floor heights (two are small landings) plus a sky platform nothing connects to, "
            f"joined by {n_stairs} staircases or ramps. The diagram shows what links to what; the cards below show "
            "each floor’s layout, where each stair starts and ends, and what’s on it.")

LIMITS_NOTE = ("The “Teleport” destination and the way into the sky platform are unknown. Floor names come from "
               "Brewall’s labels (Teritarx / Protarx / Anetarx / Penutarx look like four tiers, low to high); "
               "where a floor had no label it is described by what it connects.")
SOURCE_NOTE = ("Source: <a href=\"https://github.com/RedGuides/brewall-maps\">RedGuides/brewall-maps</a> on GitHub, "
               "commit 15f39bf. Unofficial derived guide; map data belongs to its author.")

ROUTES_TITLE = "Arx Mentis: room-to-room routes"
ROUTES_LIMITS_NOTE = ("The Teritarx Preservation Chamber is a closed outline on the map, so its route ends at its walls. "
                      "The Magicae Sanctuary cave has no closed outline, so its directions are rougher. The Teleport and "
                      "the pit are connected to each other (S1) but not to the tower, and the map doesn’t say where the "
                      "Teleport goes. The +468 sky platform isn’t included. “Crasis Whesar” and “Keeper of the Matrix” "
                      "may be NPC labels rather than rooms.")
