"""Draw one floor's wall lines with labels, ramp ends and a 10-unit grid, to divide it into rooms and corridors by hand.
Usage: python3 -I tools/plot_floor.py <zone> <map dir> <level> <out.png> [x0 x1 y0 y1]
Read x/y off the grid and use them in the zone config (CORRIDORS, FLOOR_GRAPHS, CORRIDOR_GROUPS, ROOM_BOX)."""
import os,sys
zone,mapdir,lv,out=sys.argv[1],sys.argv[2],int(sys.argv[3]),sys.argv[4]
os.environ.update(EQ_ZONE=zone,EQ_MAP_DIR=mapdir)
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import model as M, route as R
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
xs=[v for l in R.geo[lv] for v in (l[0],l[3])];ys=[v for l in R.geo[lv] for v in (l[1],l[4])]
x0,x1,y0,y1=[float(v) for v in sys.argv[5:9]] if len(sys.argv)>=9 else (min(xs)-10,max(xs)+10,min(ys)-10,max(ys)+10)
fig,ax=plt.subplots(figsize=(14,11))
for l in R.geo[lv]: ax.plot([l[0],l[3]],[l[1],l[4]],'k-',lw=.7)
for g in R.STAIRS:
    if lv==g['lo']:
        for f in g['feet']: ax.plot(*f,'ro');ax.text(f[0],f[1],g['id']+'v',color='r')
    if lv==g['hi']:
        for f in g['heads']: ax.plot(*f,'bo');ax.text(f[0],f[1],g['id']+'^',color='b')
for p in M.labs:
    if abs(p['z']-lv)<16: ax.plot(p['x'],p['y'],'g.');ax.text(p['x'],p['y'],p['t'][:22],fontsize=7,color='g')
for r_ in R.ROOMS:
    if r_['lv']==lv: ax.plot(r_['x'],r_['y'],'m+');ax.text(r_['x'],r_['y'],r_['name'],fontsize=6,color='m')
ax.set_aspect('equal');ax.set_xlim(x0,x1);ax.set_ylim(y1,y0);ax.grid(True,alpha=.35)
ax.set_xticks(range(int(x0//10*10),int(x1)+10,10));ax.set_yticks(range(int(y0//10*10),int(y1)+10,10))
plt.xticks(fontsize=6);plt.yticks(fontsize=6);plt.savefig(out,dpi=75,bbox_inches='tight')
