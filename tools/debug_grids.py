"""Draw each floor's computed walkable mask (colour = connected region), walls, and the
route nodes (rooms and stair ends).  Use it when a room comes out unreachable.

    python3 -I tools/debug_grids.py <zone> <map_dir> <out.png>
"""
import os, sys
os.environ.update(EQ_ZONE=sys.argv[1], EQ_MAP_DIR=sys.argv[2])
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import route as R

lvls = R.MAINL + R.Z.EXTRA_GRID_LEVELS
n = len(lvls); cols = 4; rows = (n + cols - 1) // cols
fig, axs = plt.subplots(rows, cols, figsize=(6 * cols, 6 * rows))
for ax in axs.flat: ax.axis('off')
for ax, lv in zip(axs.flat, lvls):
    G = R.grids[lv]
    lab, _ = ndimage.label(G.walk, np.ones((3, 3)))
    ax.imshow(lab, cmap='tab20', interpolation='nearest')
    for l in R.geo[lv]:
        ax.plot([(l[0] - G.x0) / R.RES, (l[3] - G.x0) / R.RES], [(l[1] - G.y0) / R.RES, (l[4] - G.y0) / R.RES], 'k-', lw=.5)
    for k, (l, x, y) in R.nodes.items():
        if l == lv:
            c = R.snapped[k]
            ax.plot(c[1], c[0], 'r*', ms=6)
            ax.text(c[1], c[0], (R.ROOMS[k[1]]['name'][:14] if k[0] == 'r' else k[1]), fontsize=6)
    ax.set_title(f"z={lv}"); ax.axis('on')
plt.tight_layout(); plt.savefig(sys.argv[3], dpi=55)
print("wrote", sys.argv[3])
