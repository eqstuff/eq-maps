"""First step when adding a zone: find its floor heights, stairs and labels.

    python3 -I tools/analyze_levels.py <map_dir> <file_prefix>

Prints (1) a histogram of flat wall segments by Z (peaks = floors -> LEVELS in the zone config),
(2) clusters of sloped segments with their Z range and bounding box (= stairs / ramps / terrain),
(3) the label list with Z (= candidate rooms).  Brewall draws the map key far outside the zone
(usually in <prefix>_2.txt); it is not read here.
"""
import collections, math, os, sys

map_dir, prefix = sys.argv[1], sys.argv[2]
L, P = [], []
for ln in open(os.path.join(map_dir, prefix + '.txt')):
    if ln[:1] == 'L':
        L.append([float(x) for x in ln[2:].split(',')[:6]])
lab = os.path.join(map_dir, prefix + '_1.txt')
if os.path.exists(lab):
    for ln in open(lab):
        if ln[:1] == 'P':
            p = [x.strip() for x in ln[2:].split(',')]
            P.append((float(p[0]), float(p[1]), float(p[2]), p[7]))

flat = [l for l in L if abs(l[2] - l[5]) < .5]
slope = [l for l in L if abs(l[2] - l[5]) >= .5]
print(f"{len(L)} segments: {len(flat)} flat, {len(slope)} sloped; {len(P)} labels\n")

print("== flat segments by Z (rounded to 1 unit; showing >= 3) ==")
h = collections.Counter(round((l[2] + l[5]) / 2) for l in flat)
for z in sorted(h):
    if h[z] >= 3:
        print(f"  z={z:6d}  {h[z]:4d} segs  {'#' * min(60, h[z] // 4)}")

print("\n== sloped-segment clusters (endpoints within 4 units are joined) ==")
par = list(range(len(slope)))
def find(i):
    while par[i] != i:
        par[i] = par[par[i]]
        i = par[i]
    return i
pts = [(i, tuple(l[0:3])) for i, l in enumerate(slope)] + [(i, tuple(l[3:6])) for i, l in enumerate(slope)]
for a in range(len(pts)):
    for b in range(a + 1, len(pts)):
        if math.dist(pts[a][1], pts[b][1]) < 4:
            par[find(pts[a][0])] = find(pts[b][0])
cl = collections.defaultdict(list)
for i, l in enumerate(slope):
    cl[find(i)].append(l)
rows = []
for ls in cl.values():
    zs = [l[2] for l in ls] + [l[5] for l in ls]
    xs = [l[0] for l in ls] + [l[3] for l in ls]
    ys = [l[1] for l in ls] + [l[4] for l in ls]
    rows.append((min(zs), max(zs), min(xs), max(xs), min(ys), max(ys), len(ls)))
for r in sorted(rows):
    print(f"  z {r[0]:7.1f} -> {r[1]:7.1f}   x {r[2]:7.0f}..{r[3]:<7.0f} y {r[4]:7.0f}..{r[5]:<7.0f} segs {r[6]}")

print("\n== labels (x, y, z, text) ==")
for x, y, z, t in sorted(P, key=lambda p: p[2]):
    print(f"  z={z:7.1f}  ({x:7.1f},{y:7.1f})  {t}")
