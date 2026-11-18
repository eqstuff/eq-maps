import os,math,collections,json,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from config import Z,MAP_DIR
D=MAP_DIR
NOM=Z.LEVELS
def lvl(z,tol=4.5):
    b=min(NOM,key=lambda n:abs(n[0]-z))
    return b[0] if abs(b[0]-z)<=tol else None
def load():
    L=[];P=[]
    for ln in open(os.path.join(D,Z.FILE_PREFIX+'.txt')):
        if ln[:1]=='L':
            p=[x.strip() for x in ln[2:].split(',')]; L.append([float(x) for x in p[:6]])
    import glob,re
    files=[os.path.join(D,Z.FILE_PREFIX+'.txt')]+sorted(glob.glob(os.path.join(D,Z.FILE_PREFIX+'_[0-9]*.txt')))
    for fn in files:                      # P records may be in the geometry file and in every _N layer
        for ln in open(fn,encoding='utf-8',errors='replace'):
            if ln[:1]=='P':
                p=[x.strip() for x in ln[2:].split(',')]; P.append((float(p[0]),float(p[1]),float(p[2]),','.join(p[7:])))
    return L,P
L,P=load()
flat=[l for l in L if abs(l[2]-l[5])<.5]
slope=[l for l in L if abs(l[2]-l[5])>=.5]
# floor geometry per level, used to decide which floor a ramp end belongs to
_flatpts=collections.defaultdict(list)
for _l in flat:
    _lv=Z.flat_level((_l[2]+_l[5])/2,lvl)
    if _lv is not None: _flatpts[_lv]+=[(_l[0],_l[1]),(_l[3],_l[4])]
def _end_level(z,pts,tol):
    """Floor that one end of a sloped cluster reaches.  Candidates are the levels within `tol` of z
    (plus whatever the zone's flat_level rule says, e.g. cave heights); when several fit, the one whose
    walls are nearest the end's x,y wins (a ramp ending at -5 next to the 0 floor belongs to 0)."""
    cand={n[0] for n in NOM if abs(n[0]-z)<=tol}
    c=Z.flat_level(z,lambda zz,t=tol:lvl(zz,t))
    if c is not None: cand.add(c)
    if not cand: return None
    if len(cand)==1: return next(iter(cand))
    cx=sum(p[0] for p in pts)/len(pts); cy=sum(p[1] for p in pts)/len(pts)
    def d(n): return min((math.dist((cx,cy),q) for q in _flatpts.get(n,[(1e9,1e9)])),default=1e9)
    return min(cand,key=d)
# slope clusters
par=list(range(len(slope)))
def f(i):
    while par[i]!=i: par[i]=par[par[i]]; i=par[i]
    return i
ends=[(i,tuple(l[0:3])) for i,l in enumerate(slope)]+[(i,tuple(l[3:6])) for i,l in enumerate(slope)]
for a in range(len(ends)):
    for b in range(a+1,len(ends)):
        if math.dist(ends[a][1],ends[b][1])<4: par[f(ends[a][0])]=f(ends[b][0])
cl=collections.defaultdict(list)
for i,l in enumerate(slope): cl[f(i)].append(l)
C=[]
for ls in cl.values():
    zs=[l[2] for l in ls]+[l[5] for l in ls]
    zlo,zhi=min(zs),max(zs)
    tol=getattr(Z,'STAIR_TOL',4.5)
    pts=[(l[0],l[1],l[2]) for l in ls]+[(l[3],l[4],l[5]) for l in ls]
    foot=[p for p in pts if p[2]<zlo+1.5]; head=[p for p in pts if p[2]>zhi-1.5]
    lo=_end_level(zlo,foot,tol); hi=_end_level(zhi,head,tol)
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    C.append(dict(zlo=zlo,zhi=zhi,lo=lo,hi=hi,segs=ls,bbox=[min(xs),min(ys),max(xs),max(ys)],
        foot=(sum(p[0] for p in foot)/len(foot),sum(p[1] for p in foot)/len(foot)),
        head=(sum(p[0] for p in head)/len(head),sum(p[1] for p in head)/len(head))))
stairs=[c for c in C if c['lo'] is not None and c['hi'] is not None and c['lo']!=c['hi']]
terrain=[c for c in C if c not in stairs]
# merge rails of same stair
def gap(a,b):
    ax0,ay0,ax1,ay1=a;bx0,by0,bx1,by1=b
    return max(max(bx0-ax1,ax0-bx1),max(by0-ay1,ay0-by1),0)
groups=[]
for c in stairs:
    for g in groups:
        if g['lo']==c['lo'] and g['hi']==c['hi'] and gap(g['bbox'],c['bbox'])<Z.MERGE_GAP.get(c['lo'],20):
            g['parts'].append(c); g['bbox']=[min(g['bbox'][0],c['bbox'][0]),min(g['bbox'][1],c['bbox'][1]),max(g['bbox'][2],c['bbox'][2]),max(g['bbox'][3],c['bbox'][3])]; break
    else: groups.append(dict(lo=c['lo'],hi=c['hi'],parts=[c],bbox=list(c['bbox'])))
groups.sort(key=lambda g:(g['lo'],g['hi'],g['bbox'][0]))
for i,g in enumerate(groups):
    g['id']="S%d"%(i+1)
    segs=[s for p in g['parts'] for s in p['segs']]
    g['nseg']=len(segs)
    fx=[p['foot'] for p in g['parts']]; hx=[p['head'] for p in g['parts']]
    g['foot']=(sum(a for a,b in fx)/len(fx),sum(b for a,b in fx)/len(fx))
    g['head']=(sum(a for a,b in hx)/len(hx),sum(b for a,b in hx)/len(hx))

def _clusters(pts,r=25):
    cs=[]
    for p in pts:
        for c in cs:
            if math.dist(c['c'],p)<r:
                c['p'].append(p); c['c']=(sum(q[0] for q in c['p'])/len(c['p']),sum(q[1] for q in c['p'])/len(c['p'])); break
        else: cs.append(dict(c=p,p=[p]))
    return [c['c'] for c in cs]
for g in groups:
    segs=[s for p in g['parts'] for s in p['segs']]
    zl_=min(min(s[2],s[5]) for s in segs); zh_=max(max(s[2],s[5]) for s in segs)
    PP=[]
    for s in segs: PP+=[(s[0],s[1],s[2]),(s[3],s[4],s[5])]
    g['feet']=_clusters([(p[0],p[1]) for p in PP if p[2]<zl_+1.5])
    g['heads']=_clusters([(p[0],p[1]) for p in PP if p[2]>zh_-1.5])
# labels with level
labs=[]
for x,y,z,t in P:
    labs.append(dict(x=x,y=y,z=z,t=t.replace('_',' '),lv=lvl(z,12) ))
if __name__=="__main__":
    print(len(groups),"stairs;",len(terrain),"terrain slopes")
    for g in groups: print(g['id'],g['lo'],'->',g['hi'],[round(v) for v in g['bbox']],'segs',g['nseg'],'foot',[round(v) for v in g['foot']],'head',[round(v) for v in g['head']])
    print("terrain:")
    for c in terrain: print(round(c['zlo']),round(c['zhi']),[round(v) for v in c['bbox']],len(c['segs']))
    for l in labs: print(l['lv'],round(l['z']),l['t'])
