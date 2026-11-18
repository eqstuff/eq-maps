"""Zone configuration for Arx Mentis (map: Good's Maps, files arxmentis.txt / _1 / _2 / _3).

Everything zone-specific lives here; the tools in tools/ are generic.  To map another
zone, copy this file to tools/zones/<zone>.py and edit it (see docs/ADAPTING.md).
"""
import re
FILE_PREFIX = "arxmentis"          # arxmentis.txt (geometry) + arxmentis_1/_2/_3.txt (label layers)
TITLE = "Arx Mentis: floors and connections"

# --- floors -----------------------------------------------------------------
# (nominal map Z, short name).  Found by histogramming the Z of flat wall segments
# (see docs/DESIGN.md).  A segment belongs to the nearest level within 4.5 units.
LEVELS = [(-483, "Pit floor"), (-430, "Teleport cross"), (-70, "Lower vaults"),
          (-35, "Garden level"), (-5, "Ground south annex"), (0, "Ground"),
          (24, "Relic Keep"), (45, "East landing"), (80, "Study level"),
          (85, "Landing +85"), (105, "Landing +105"), (115, "Magicae cave"),
          (172, "Upper level"), (470, "Sky platform")]
FLOOR_NAMES = {470: "Unlabeled sky platform", 172: "Penutarx: upper labs",
               115: "Anetarx: Magicae Sanctuary (cave)", 105: "West corridor landing (+105)",
               85: "West corridor (+85)", 80: "Anetarx: study level", 45: "East landing",
               24: "Protarx: Relic Keep", 0: "Ground: central hub", -5: "Ground south annex",
               -35: "Protarx: gardens & library", -70: "Teritarx: preservation vaults",
               -430: "Teleport cross", -483: "Pit: merchants & quest hall"}
ROUTE_NAMES = {172: "Upper labs", 115: "Magicae cave", 105: "West corridor (+105)",
               85: "West corridor (+85)", 80: "Study level", 45: "East landing",
               24: "Relic Keep level", 0: "Ground", -5: "Ground south annex",
               -35: "Gardens level", -70: "Preservation vaults", -430: "Teleport cross",
               -483: "Pit"}
FLOOR_ORDER = [470, 172, 115, 105, 85, 80, 45, 24, 0, -5, -35, -70, -430, -483]  # top to bottom
MINOR_LEVELS = (105, 85, -5, 470)   # drawn with dashed boxes (landings / annexes)
SKY_LEVELS = (470,)                 # geometry nothing connects to: not selectable in the UI

# --- links between floors -----------------------------------------------------
# Good's draws a ramp/stair as one or two long sloped lines whose ends stop short of the
# floors, so link ends are matched to floors with a wider tolerance than flat walls.
STAIR_TOL = 9
# Pieces of one link that start within this many units are merged into one link.
# The pit's four ramps meet at the teleport cross, so they need a wider gap.
MERGE_GAP = {-483: 80}

# --- cave / irregular floors ------------------------------------------------
OPEN_LEVELS = (115,)
CAVE_LEVEL = 115
CAVE_MIN_Z = 105

def flat_level(z, lvl):
    """Level for a flat segment at height z.  `lvl(z)` is the nearest-level helper."""
    if 108 <= z <= 135:             # irregular cave floor heights all collapse to +115
        return 115
    if 90 <= z < 108 and lvl(z) is None:
        return 115
    if 172 <= z <= 180:             # a raised platform inside the upper labs
        return 172
    return lvl(z)

def label_level(z, lvl):
    """Level for a P (label) record at height z; labels float above/below floors."""
    if 108 <= z <= 135:
        return 115
    return lvl(z, 15)

def room_level(t, z, lvl):
    """Rooms whose label height is off.  Good's puts the Protarx Gardens label at -3.7 although the
    gardens are the -35 level (Brewall's map agrees)."""
    if clean_label(t) == "Protarx Gardens":
        return -35
    return label_level(z, lvl)

# --- rooms (named destinations) ----------------------------------------------
# Good's has no separate "room" layer: rooms, NPCs, mission markers and zone lines are all P labels.
# So rooms are an explicit list: cleaned label text -> display name.
ROOM_LABELS = {
    "Penutarx Junction": "Penutarx Junction", "Protarx Infusion Lab": "Protarx Infusion Lab",
    "Anetax Armory": "Anetarx Armory", "Penutarx Stasis Lab": "Penutarx Stasis Lab",
    "Penutarx Reanimation Ward": "Penutarx Reanimation Ward",
    "Anetarx Extraction Lab": "Anetarx Extraction Lab", "Anetarx Central Study": "Anetarx Central Study",
    "Protarx Relic Keep": "Protarx Relic Keep", "Anetarx Magicae Sanctuary": "Anetarx Magicae Sanctuary",
    "Protarx Gardens": "Protarx Gardens", "Protarx Library": "Protarx Library",
    "the study": "Protarx Study", "Teritarx Preservation Chamber": "Teritarx Preservation Chamber",
    "Keeper of the Matrix": "Keeper of the Matrix", "Analysis room": "Analysis Room",
    "Medical Chamber": "Medical Chamber", "Feeding Chamber": "Feeding Chamber",
    "First Generator": "First Generator", "Second Generator": "Second Generator",
    "Third Generator": "Third Generator",
}
def clean_label(t):
    return re.sub(r"\s+", " ", t.replace("_", " ")).strip()
def is_room_label(t):
    return clean_label(t) in ROOM_LABELS
def room_name(t):
    return ROOM_LABELS[clean_label(t)]

# What the other labels are.  Returns a search-result kind, or None to leave the label out.
def label_kind(t):
    c = clean_label(t); low = c.lower()
    if low.startswith("map by") or low.startswith("original map"): return None
    if low.endswith("-gs") or low.startswith("gs:"): return None          # collection ground spawns
    if low.startswith("to ") or "portal" in low: return "zone connection"
    if low.startswith("the unseen"): return None                         # repeated marker, not a place
    return "NPC / point"
def label_text(t):
    c = re.sub(r"\s*\(", " (", re.sub(r"\)(?=\w)", ") ", clean_label(t)))
    while c.count(")") > c.count("(") and c.endswith(")"):               # stray ")" from "Name(Q)ROAM)"
        c = c[:-1].rstrip()
    c = c + ")" * (c.count("(") - c.count(")"))                          # Good's truncates some names
    return c[:1].upper() + c[1:]

# Rooms that have no label in the map but are useful waypoints: (name, x, y, level)
EXTRA_ROOMS = [("Teleport", 1, -108, -430),
               ("Central hub (ground)", 0, 0, 0),
               ("Pit (merchants / Firiona Vie)", 0, -20, -483)]

# --- teleports (not in the map file) ------------------------------------------
# Links between two named rooms on different floors.  Added to the route graph as an
# extra connection (two-way).  Source: in-game experience of the repo owner; Good's map labels a "portal" at the cross
# and a "Portal out" at the hub centre, which fits.
PORTALS = [dict(id="T1", name="Teleport",
                from_room="Teleport", to_room="Central hub (ground)", cost=20,
                text="The teleport pad at the top of the pit pyramid. It is reported to land you at the "
                     "four-way crossing of the ground-floor central hub. Good’s map marks a “portal” at the "
                     "cross and a “Portal out” at the middle of that hub.")]

# --- walkable grids ---------------------------------------------------------
STRAIGHT_ROUTES = True    # Good's outlines have gaps, so no walkable grid: straight-line headings only
GRID_LEVELS = [172, 115, 105, 85, 80, 45, 24, 0, -5, -35, -70]    # the connected tower
EXTRA_GRID_LEVELS = [-430, -483]                                    # cut off from the tower

# --- page text --------------------------------------------------------------
def floor_note(lv):
    notes = {
        115: '<p class="note">This is a natural cave, so Good’s draws it with irregular sloped edges rather than clean ramps.</p>',
        470: '<p class="note">A square hall with round pillars, about 470 units above the ground floor. No ramps or labels reach it, so the file doesn’t say how you get there (probably a teleport destination).</p>',
        -430: '<p class="note">A cross-shaped platform at the top of the pit pyramid. Good’s labels a “portal” here. The four long ramps lead down to the pit floor. The map file doesn’t say where the portal leads; the <b>T1</b> link to the central hub comes from in-game experience, and Good’s “Portal out” label sits in the middle of that hub.</p>',
    }
    return notes.get(lv, "")

def intro(n_stairs):
    return ("Decoded from Good’s map files (<code>arxmentis.txt</code> and its <code>_1</code>, <code>_2</code>, <code>_3</code> label layers). "
            "The zone has 13 floor heights (three are small landings or annexes) plus a sky platform nothing connects to, "
            f"joined by {n_stairs} ramps and stairs. The diagram shows what links to what; the cards below show "
            "each floor’s layout, where each link starts and ends, and what’s on it.")

LIMITS_NOTE = ("The way into the sky platform is unknown, and the teleport link (T1) is added from in-game experience rather than read from the map. Floor names come from "
               "Good’s room labels (Teritarx / Protarx / Anetarx / Penutarx look like four tiers, low to high); "
               "where a floor had no label it is described by what it connects. Directions are straight lines between points: "
               "Good’s outlines have gaps, so the walls aren’t used to find a path.")
SOURCE_NOTE = ("Source: <a href=\"https://github.com/RedGuides/goodurden-maps\">RedGuides/goodurden-maps</a> on GitHub "
               "(Good’s Maps, by Goodurden), commit 29b1480. Unofficial derived guide; map data belongs to its author.")

ROUTES_TITLE = "Arx Mentis: room-to-room routes"
ROUTES_LIMITS_NOTE = ("Directions are straight-line compass headings between the room, the ramp ends and the next room; "
                      "walls aren’t considered, so follow the corridors toward that heading. The pit and the teleport cross "
                      "connect to the tower only through the teleport link T1 (central hub), which comes from in-game "
                      "experience, not from the map, and is assumed to work both ways. The +470 sky platform isn’t included.")
