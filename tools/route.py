import os,sys,math,json,collections,heapq
import numpy as np
if __name__=='__main__' and len(sys.argv)>=3:
    os.environ.update(EQ_ZONE=sys.argv[1],EQ_MAP_DIR=sys.argv[2])
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from config import Z
import model as M
from scipy import ndimage
from skimage.graph import MCP_Geometric
from skimage.measure import approximate_polygon
import networkx as nx
NAMES=Z.ROUTE_NAMES
def zl(z): return ("+%d"%z) if z>0 else str(z)
def flat_level(z): return Z.flat_level(z,M.lvl)
geo=collections.defaultdict(list)
for l in M.flat:
    lv=flat_level((l[2]+l[5])/2)
    if lv is not None: geo[lv].append(l)
# ----- rooms (named destinations)
ROOMS=[]
for p in M.labs:
    t=p['t']
    if not Z.is_room_label(t): continue
    ROOMS.append(dict(name=t,x=p['x'],y=p['y'],lv=Z.label_level(p['z'],M.lvl)))
# labels that appear more than once get a floor suffix
_cnt=collections.Counter(r_['name'] for r_ in ROOMS)
for r_ in ROOMS:
    if _cnt[r_['name']]>1: r_['name']='%s (%s)'%(r_['name'],zl(r_['lv']))
for name,x,y,lv in Z.EXTRA_ROOMS: ROOMS.append(dict(name=name,x=x,y=y,lv=lv))
for i,r in enumerate(ROOMS): r['id']=i
STAIRS=M.groups
# ----- grids
RES=1.0
class Grid: pass
grids={}
def build_grid(lv):
    segs=geo[lv]
    xs=[];ys=[]
    for l in segs: xs+=[l[0],l[3]]; ys+=[l[1],l[4]]
    for g in STAIRS:
        if lv in (g['lo'],g['hi']): xs+=[g['bbox'][0],g['bbox'][2]]; ys+=[g['bbox'][1],g['bbox'][3]]
    for r in ROOMS:
        if r['lv']==lv: xs.append(r['x']); ys.append(r['y'])
    G=Grid(); G.x0=min(xs)-15; G.y0=min(ys)-15
    G.W=int((max(xs)+15-G.x0)/RES)+1; G.H=int((max(ys)+15-G.y0)/RES)+1
    wall=np.zeros((G.H,G.W),bool)
    for l in segs:
        n=max(2,int(math.hypot(l[3]-l[0],l[4]-l[1])/0.4))
        t=np.linspace(0,1,n)
        cx=((l[0]+(l[3]-l[0])*t-G.x0)/RES).astype(int); cy=((l[1]+(l[4]-l[1])*t-G.y0)/RES).astype(int)
        wall[cy,cx]=True
    wall=ndimage.binary_dilation(wall,np.ones((3,3)))
    sl=np.zeros_like(wall)
    for g in STAIRS:
        if lv in (g['lo'],g['hi']):
            for p in g['parts']:
                for s_ in p['segs']:
                    n=max(2,int(math.hypot(s_[3]-s_[0],s_[4]-s_[1])/0.4)); t=np.linspace(0,1,n)
                    cx=((s_[0]+(s_[3]-s_[0])*t-G.x0)/RES).astype(int); cy=((s_[1]+(s_[4]-s_[1])*t-G.y0)/RES).astype(int)
                    sl[cy,cx]=True
    wf=ndimage.binary_dilation(wall|sl,np.ones((3,3)),iterations=2)
    lab_,n_=ndimage.label(~wf)
    border=set(np.unique(np.concatenate([lab_[0],lab_[-1],lab_[:,0],lab_[:,-1]])))-{0}
    ext=np.isin(lab_,list(border))
    inside=~ext
    if lv in Z.OPEN_LEVELS: inside=np.ones_like(wall)
    stm=np.zeros_like(wall)
    for g in STAIRS:
        if lv in (g['lo'],g['hi']):
            for p in g['parts']:
                bx0,by0,bx1,by1=p['bbox']
                if (bx1-bx0)<30 or (by1-by0)<30:
                    stm[int((by0-G.y0)/RES):int((by1-G.y0)/RES)+1,int((bx0-G.x0)/RES):int((bx1-G.x0)/RES)+1]=True
                else:
                    for s_ in p['segs']:
                        n=max(2,int(math.hypot(s_[3]-s_[0],s_[4]-s_[1])/0.4)); t=np.linspace(0,1,n)
                        cx=((s_[0]+(s_[3]-s_[0])*t-G.x0)/RES).astype(int); cy=((s_[1]+(s_[4]-s_[1])*t-G.y0)/RES).astype(int)
                        stm[cy,cx]=True
    stm=ndimage.binary_dilation(stm,np.ones((3,3)),iterations=2)
    G.walk=(inside|stm)&~(wall&~stm)
    G.walk&= True
    grids[lv]=G
    return G
def cell(G,x,y): return (min(G.H-1,max(0,int((y-G.y0)/RES))),min(G.W-1,max(0,int((x-G.x0)/RES))))
def snap(G,x,y):
    c=cell(G,x,y)
    if G.walk[c]: return c,0
    d,idx=ndimage.distance_transform_edt(~G.walk,return_indices=True)
    r,cc=idx[0][c],idx[1][c]
    return (int(r),int(cc)),float(d[c])
MAINL=Z.GRID_LEVELS
for lv in MAINL+Z.EXTRA_GRID_LEVELS: build_grid(lv)
# nodes on floors
nodes={}   # key -> (lv,cell)
for r in ROOMS: nodes[('r',r['id'])]=(r['lv'],r['x'],r['y'])
for g in STAIRS:
    for i,f_ in enumerate(g['feet']): nodes[('s',g['id'],g['lo'],'f%d'%i)]=(g['lo'],f_[0],f_[1])
    for i,h_ in enumerate(g['heads']): nodes[('s',g['id'],g['hi'],'h%d'%i)]=(g['hi'],h_[0],h_[1])
snapped={};bad=[]
for k,(lv,x,y) in nodes.items():
    c,d=snap(grids[lv],x,y); snapped[k]=c
    if d>25: bad.append((k,lv,round(d)))
print("far-snap nodes:",bad)
SEALED={}
for lv in MAINL+Z.EXTRA_GRID_LEVELS:
    Gd=grids[lv]; lab,n=ndimage.label(Gd.walk,np.ones((3,3)))
    sizes=ndimage.sum(Gd.walk,lab,range(1,n+1)); big=int(np.argmax(sizes))+1
    for k in list(snapped):
        if nodes[k][0]==lv and k[0]=='r':
            c=snapped[k]
            if lab[c]!=big and sizes[lab[c]-1]<1500:
                d,idx=ndimage.distance_transform_edt(lab!=big,return_indices=True)
                snapped[k]=(int(idx[0][c]),int(idx[1][c])); SEALED[k]=True
print("sealed rooms:",[ROOMS[k[1]]['name'] for k in SEALED])
HDG=['N','NE','E','SE','S','SW','W','NW']
def hd(dx,dy):
    a=math.degrees(math.atan2(dx,-dy))%360
    return HDG[int((a+22.5)//45)%8]
def legs_from(cells,G):
    pts=np.array([[G.x0+(c+0.5)*RES,G.y0+(r+0.5)*RES] for r,c in cells])
    if len(pts)<2: return []
    ap=approximate_polygon(pts,tolerance=7)
    raw=[]
    for a,b in zip(ap[:-1],ap[1:]):
        raw.append([hd(b[0]-a[0],b[1]-a[1]),math.hypot(*(b-a))])
    out=[]
    for h,l in raw:
        if l<14 and len(raw)>1: continue
        if out and out[-1][0]==h: out[-1][1]+=l
        else: out.append([h,l])
    return [(h,max(10,int(round(l/10.0))*10)) for h,l in out]
G=nx.Graph()
fl=collections.defaultdict(list)
for k,(lv,x,y) in nodes.items(): fl[lv].append(k)
within={}
for lv,ks in fl.items():
    Gd=grids[lv]; cost=np.where(Gd.walk,1.0,np.inf)
    for a in ks:
        mcp=MCP_Geometric(cost,fully_connected=True)
        cum,_=mcp.find_costs([snapped[a]])
        for b in ks:
            if a==b: continue
            d=cum[snapped[b]]
            if np.isfinite(d):
                within[(a,b)]=(float(d),legs_from(mcp.traceback(snapped[b]),Gd))
                G.add_edge(a,b,weight=float(d)+1)
for g in STAIRS:
    for i,f_ in enumerate(g['feet']):
        for j,h_ in enumerate(g['heads']):
            a=('s',g['id'],g['lo'],'f%d'%i);b=('s',g['id'],g['hi'],'h%d'%j)
            ln=math.sqrt((abs(f_[0]-h_[0])+abs(f_[1]-h_[1]))**2+(g['hi']-g['lo'])**2)
            G.add_edge(a,b,weight=ln,stair=g['id'])
PORTALS=[]
_byname={r_['name']:r_ for r_ in ROOMS}
for p_ in getattr(Z,'PORTALS',[]):
    a_,b_=_byname.get(p_['from_room']),_byname.get(p_['to_room'])
    if a_ and b_:
        PORTALS.append(dict(id=p_['id'],name=p_['name'],a=a_['id'],b=b_['id'],text=p_.get('text','')))
        G.add_edge(('r',a_['id']),('r',b_['id']),weight=float(p_.get('cost',20)),portal=p_['id'])
def fmt(legs): return ", then ".join("%s %d"%(h,l) for h,l in legs) or "a few steps"
def route(a,b):
    ka,kb=('r',a),('r',b)
    if ka not in G or kb not in G or not nx.has_path(G,ka,kb): return None
    p=nx.shortest_path(G,ka,kb,weight='weight')
    steps=[];dist=0;nst=0
    ri={r['id']:r for r in ROOMS}
    i=0
    while i<len(p)-1:
        u,v=p[i],p[i+1]
        if G.edges[u,v].get('portal'):
            steps.append(dict(k='portal',id=G.edges[u,v]['portal'],fr=nodes[u][0],to=nodes[v][0],toname=NAMES.get(nodes[v][0],'')))
            dist+=G.edges[u,v]['weight']
        elif G.edges[u,v].get('stair') and u[0]=='s' and v[0]=='s' and u[1]==v[1] and u[2]!=v[2]:
            g=[s for s in STAIRS if s['id']==u[1]][0]
            up=v[2]>u[2]; nst+=1
            steps.append(dict(k='stair',id=g['id'],dir='up' if up else 'down',to=v[2],toname=NAMES[v[2]]))
            dist+=G.edges[u,v]['weight']
        else:
            d,legs=within[(u,v)]; dist+=d
            tgt=('stairs '+v[1]) if v[0]=='s' else ri[v[1]]['name']
            steps.append(dict(k='walk',legs=legs,to=tgt,lv=nodes[u][0],toR=(v[0]=='r'),fromR=(u[0]=='r'),xy=(nodes[v][1],nodes[v][2]),sealed=(v in SEALED)))
        i+=1
    return dict(steps=steps,dist=int(dist),stairs=nst)
if __name__=="__main__":
    ids=[r['id'] for r in ROOMS]
    miss=[(ROOMS[a]['name'],ROOMS[b]['name']) for a in ids for b in ids if a!=b and route(a,b) is None]
    print(len(ROOMS),"rooms; unreachable pairs:",len(miss))
    comps=[ [ROOMS[i]['name'] for i in ids if ('r',i) in c] for c in nx.connected_components(G) ]
    for c in comps: 
        if any(c): print([x for x in c])
    r=route(7,13) if len(ROOMS)>13 else None
    for r_ in ROOMS: print(r_['id'],r_['lv'],r_['name'])
