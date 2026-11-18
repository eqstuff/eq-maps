import os,sys,html,json,math,collections
if __name__=='__main__' and len(sys.argv)>=4:
    os.environ.update(EQ_ZONE=sys.argv[1],EQ_MAP_DIR=sys.argv[2],EQ_OUT_DIR=sys.argv[3])
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from config import Z,OUT_DIR
import model as M
import route as R
import networkx as nx
E=html.escape
OUT=sys.argv[1] if False else None
NAMES=Z.FLOOR_NAMES
ORDER=Z.FLOOR_ORDER
def zl(z): return ("+%d"%z) if z>0 else str(z)
def flat_level(z):
    return Z.flat_level(z,M.lvl)
# geometry per level
geo=collections.defaultdict(list)
for l in M.flat:
    lv=flat_level((l[2]+l[5])/2)
    if lv is not None: geo[lv].append(l)
terr=collections.defaultdict(list)
for c in M.terrain:
    if Z.CAVE_LEVEL is not None and c['zlo']>=Z.CAVE_MIN_Z: terr[Z.CAVE_LEVEL]+=c['segs']
# stairs
st=M.groups
byl=collections.defaultdict(list)
for g in st: byl[g['lo']].append(g); byl[g['hi']].append(g)
pois=collections.defaultdict(list)
for p in M.labs:
    lv=Z.label_level(p['z'],M.lvl)
    pois[lv].append(p)
def near_poi(lv,xy,maxd=90):
    best=None
    for p in pois.get(lv,[]):
        if p['t'].startswith('to #'): continue
        d=math.dist((p['x'],p['y']),xy)
        if d<maxd and (best is None or d<best[0]): best=(d,p['t'])
    return best[1] if best else None
def loc(xy): return "%d, %d"%(round(-xy[1]),round(-xy[0]))
def clean(t): return t+')'*(t.count('(')-t.count(')'))
def short(t): return clean(t)
# ---------- connection diagram (interactive) ----------
rooms_by_lv=collections.defaultdict(list)
for r_ in R.ROOMS: rooms_by_lv[r_['lv']].append(r_)
x0=46;boxw=480;laneg=16;gap=14;CHIPR=boxw-100
BOX={};y=0
chipsof={}
for lv in ORDER:
    chips=[];cx=62;line=0
    for r_ in rooms_by_lv.get(lv,[]):
        w=len(r_['name'])*6.2+16
        if cx+w>CHIPR and cx>62: line+=1;cx=62
        chips.append((r_,cx,line,w));cx+=w+6
    chipsof[lv]=chips
    h=40 if not chips else 36+(line+1)*26+2
    BOX[lv]=dict(y=y,h=h);y+=h+gap
ri={lv:i for i,lv in enumerate(ORDER)}
edges=[(ri[g['hi']],ri[g['lo']],g) for g in st]
lanes=[]
for e in sorted(edges,key=lambda e:(e[1]-e[0])):
    for ln in lanes:
        if all(e[1]<a_ or e[0]>b_ for a_,b_,_ in ln): ln.append((e[0],e[1],e[2])); break
    else: lanes.append([(e[0],e[1],e[2])])
laneof={}
for k,ln in enumerate(lanes):
    for a_,b_,g in ln: laneof[g['id']]=k
cnt=collections.defaultdict(list)
for a_,b_,g in sorted(edges,key=lambda e:(laneof[e[2]['id']])):
    cnt[ORDER[a_]].append(g['id']); cnt[ORDER[b_]].append(g['id'])
ANCH={}
for lv,lst in cnt.items():
    n=len(lst);bx=BOX[lv]
    for k,gid in enumerate(lst):
        ANCH["%s@%d"%(gid,lv)]=round(bx['y']+10+(k*(bx['h']-20)/(n-1) if n>1 else (bx['h']-20)/2),1)
W=x0+boxw+30+len(lanes)*laneg+40;H=y
cols=['#c2410c','#1d4ed8','#047857','#a21caf','#b45309','#0e7490','#be123c','#4d7c0f']
svg=[f'<svg viewBox="0 0 {W} {H}" class="diag" role="img" aria-label="Floor connection diagram">']
for a_,b_,g in edges:
    k=laneof[g['id']];lx=x0+boxw+22+k*laneg;c=cols[k%len(cols)]
    ya=ANCH["%s@%d"%(g['id'],ORDER[a_])];yb=ANCH["%s@%d"%(g['id'],ORDER[b_])]
    svg.append(f'<g class="edge" id="e-{g["id"]}"><title>{g["id"]}: {zl(g["lo"])} {E(NAMES[g["lo"]])} to {zl(g["hi"])} {E(NAMES[g["hi"]])}</title><path d="M{x0+boxw} {ya:.1f} H{lx} V{yb:.1f} H{x0+boxw}" fill="none" stroke="{c}" stroke-width="1.6"/>'
      f'<circle cx="{lx}" cy="{(ya+yb)/2:.1f}" r="9" fill="{c}"/><text x="{lx}" y="{(ya+yb)/2+3.2:.1f}" class="pill" text-anchor="middle">{g["id"][1:]}</text></g>')
for lv in ORDER:
    bx=BOX[lv];yy=bx['y']
    cls='box faint' if lv in Z.MINOR_LEVELS else 'box'
    sub=' no labels, no stairs found' if (not chipsof[lv] and not byl.get(lv)) else ''
    o=[f'<g class="bx" data-lv="{lv}"><rect class="{cls}" x="{x0}" y="{yy}" width="{boxw}" height="{bx["h"]}" rx="8"/>'
       f'<text class="zt" x="{x0+10}" y="{yy+23}">{zl(lv)}</text><text class="nt" x="{x0+62}" y="{yy+23}">{E(NAMES[lv])}</text>'+(f'<text class="st" x="{x0+62+len(NAMES[lv])*7.6+14}" y="{yy+23}">{sub}</text>' if sub else '')]
    for r_,cx,line,w in chipsof[lv]:
        o.append(f'<g class="rc" data-r="{r_["id"]}"><rect x="{x0+cx:.1f}" y="{yy+34+line*26}" width="{w:.1f}" height="21" rx="10.5"/><text x="{x0+cx+w/2:.1f}" y="{yy+48.5+line*26}" text-anchor="middle">{E(r_["name"])}</text></g>')
    o.append('</g>')
    svg.append("".join(o))
svg.append('</svg>')
diagram="\n".join(svg)

# ---------- route data for the interactive diagram ----------
GR=R.G
def lvl_of(code): return code[1] if code[0]=='f' else R.ROOMS[code[1]]['lv']
def dirglyph(h): return {'N':'↑','NE':'↗','E':'→','SE':'↘','S':'↓','SW':'↙','W':'←','NW':'↖'}.get(h,'')
def legs_txt(l): return " → ".join("<b>%s</b> %d"%(h,d) for h,d in l) if l else "a few steps"
def route_entry(sk,dk):
    la,lb=lvl_of(sk),lvl_of(dk)
    if sk[0]=='f' or dk[0]=='f':
        if la==lb: return dict(h="<p class='sub'>Both are on the same floor, so no stairs are needed.</p>",s=[],f=[la])
    tmp=[]
    def add(k):
        if k[0]=='f':
            vk=('v',k[1],len(tmp)); 
            for n,(lv_,x_,y_) in R.nodes.items():
                if lv_==k[1] and n in GR: GR.add_edge(vk,n,weight=1)
            tmp.append(vk); return vk
        return ('r',k[1])
    a=add(sk);b=add(dk)
    try:
        if a not in GR or b not in GR or not nx.has_path(GR,a,b): return None
        P=nx.shortest_path(GR,a,b,weight='weight')
    finally:
        GR.remove_nodes_from([t for t in tmp if t in GR])
    sv=P[0][0]=='v';ev=P[-1][0]=='v'
    Q=P[1 if sv else 0:len(P)-1 if ev else len(P)]
    A_=R.ROOMS[sk[1]]['name'] if sk[0]=='r' else None;B_=R.ROOMS[dk[1]]['name'] if dk[0]=='r' else None
    h=[];stairs=[];floors=[la];pend=''
    if sv: h.append(f"<li>Start anywhere on <b>{zl(la)} {E(NAMES[la])}</b>.</li>")
    first=not sv
    for u,v in zip(Q[:-1],Q[1:]):
        if u[0]=='s' and v[0]=='s' and u[1]==v[1] and u[2]!=v[2]:
            up=v[2]>u[2]
            stairs.append(dict(id=u[1],dir='up' if up else 'down',fr=u[2],to=v[2],exit=pend))
            floors.append(v[2])
            h.append(f"<li><span class='chip'>{u[1]}</span> {'▲ up' if up else '▼ down'} the stairs to <b>{zl(v[2])}</b> ({E(NAMES[v[2]])})</li>")
            pend=''
        else:
            d_,legs=R.within[(u,v)]
            hd=legs[0][0] if legs else ''
            if first and u[0]=='r': head=f"Leave <b>{E(R.ROOMS[u[1]]['name'])}</b> heading <b class='dir'>{hd} {dirglyph(hd)}</b>"
            else: head=f"Head <b class='dir'>{hd} {dirglyph(hd)}</b>" if hd else "Head"
            first=False
            if v[0]=='r': tail=f"to <b>{E(R.ROOMS[v[1]]['name'])}</b>"+(" <span class='sub'>(closed outline on the map: walk up to its walls and look for the door)</span>" if v in R.SEALED else "")
            else:
                n_=R.nodes[v]; tail=f"to the <span class='chip'>{v[1]}</span> stairs <span class='sub'>(/loc {loc((n_[1],n_[2]))})</span>"
            h.append(f"<li>{head}: {legs_txt(legs)} {tail}</li>")
            pend=hd
    h.append(f"<li class='done'>Arrive at <b>{E(B_) if B_ else zl(lb)+' '+E(NAMES[lb])}</b>.</li>")
    return dict(h="<ol class='route'>"+"".join(h)+"</ol>",s=stairs,f=floors)
EPS=[('f',lv) for lv in ORDER if lv not in Z.SKY_LEVELS]+[('r',r_['id']) for r_ in R.ROOMS]
def ecode(e): return ('F%d'%e[1]) if e[0]=='f' else ('R%d'%e[1])
ROUTES={}
for ea in EPS:
    for eb in EPS:
        if ea==eb: continue
        d=route_entry(ea,eb)
        if d: ROUTES[ecode(ea)+'|'+ecode(eb)]=d
open(os.path.join(OUT_DIR,'routes.json'),'w').write(json.dumps(ROUTES,separators=(',',':')))
print('routes',len(ROUTES))
# ---------- floor plans ----------
def plan(lv):
    segs=geo.get(lv,[]); tsegs=terr.get(lv,[])
    stl=byl.get(lv,[])
    xs=[];ys=[]
    for l in segs+tsegs: xs+= [l[0],l[3]]; ys+=[l[1],l[4]]
    for g in stl:
        xs+=[g['bbox'][0],g['bbox'][2]]; ys+=[g['bbox'][1],g['bbox'][3]]
    for p in pois.get(lv,[]): xs.append(p['x']); ys.append(p['y'])
    if not xs: return '',0
    x0_,x1_,y0_,y1_=min(xs)-12,max(xs)+12,min(ys)-12,max(ys)+12
    w,h=x1_-x0_,y1_-y0_
    sc=min(600/w,520/h); sc=min(sc,6)
    Wd,Hd=w*sc,h*sc
    T=lambda x,y:((x-x0_)*sc,(y-y0_)*sc)
    o=[f'<svg viewBox="0 0 {Wd:.0f} {Hd:.0f}" class="plan" style="max-width:{Wd:.0f}px" role="img" aria-label="Plan of {E(NAMES[lv])}">']
    # other-floor stairs ghost: skip
    for l in tsegs:
        a=T(l[0],l[1]);b=T(l[3],l[4]); o.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" class="ter"/>')
    for l in segs:
        a=T(l[0],l[1]);b=T(l[3],l[4]); o.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" class="wall"/>')
    for g in stl:
        for p in g['parts']:
            for s in p['segs']:
                a=T(s[0],s[1]);b=T(s[3],s[4]); o.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" class="stair"/>')
        cx,cy=T((g['bbox'][0]+g['bbox'][2])/2,(g['bbox'][1]+g['bbox'][3])/2)
        up= g['lo']==lv
        o.append(f'<g class="pillg"><rect x="{cx-13:.1f}" y="{cy-8:.1f}" width="26" height="16" rx="8"/><text x="{cx:.1f}" y="{cy+4:.2f}" text-anchor="middle">{g["id"]}</text></g>')
    k=0
    for p in pois.get(lv,[]):
        k+=1; cx,cy=T(p['x'],p['y'])
        o.append(f'<g class="poig"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="7"/><text x="{cx:.1f}" y="{cy+3.2:.1f}" text-anchor="middle">{k}</text></g>')
    o.append('</svg>')
    return "\n".join(o),len(pois.get(lv,[]))
def headout(lv,g):
    ends=[k for k in R.nodes if k[0]=='s' and k[1]==g['id'] and R.nodes[k][0]==lv]
    outs=[]
    for r_ in rooms_by_lv.get(lv,[]):
        best=None
        for e in ends:
            v=R.within.get((('r',r_['id']),e))
            if v and (best is None or v[0]<best[0]): best=v
        if best and best[1]: outs.append(f"{E(r_['name'])} → <b>{best[1][0][0]}</b>")
    return ('<div class="sub">Heading out from: '+' · '.join(outs)+'</div>') if outs else ''
cards=[]
for lv in ORDER:
    pl,_=plan(lv)
    conn=[]
    for g in sorted(byl.get(lv,[]),key=lambda g:g['id']):
        if g['lo']==lv:
            other=g['hi'];way="up";here=g['foot'];there=g['head'];arrow="↑"
        else:
            other=g['lo'];way="down";here=g['head'];there=g['foot'];arrow="↓"
        nr=near_poi(other,there); nh=near_poi(lv,here)
        conn.append(f'<li><span class="chip">{g["id"]}</span> {arrow} <b>{way} to {zl(other)} {E(NAMES[other])}</b>'
          +headout(lv,g)+f'<div class="sub">enter at /loc {loc(here)}'+(f', near {E(short(nh))}' if nh else '')+f' · arrive /loc {loc(there)}'+(f', near {E(short(nr))}' if nr else '')+'</div></li>')
    pl_list=[]
    for i,p in enumerate(pois.get(lv,[]),1):
        pl_list.append(f'<li><span class="num">{i}</span>{E(short(p["t"]))}<span class="loc"> /loc {loc((p["x"],p["y"]))}</span></li>')
    note=""
    note=Z.floor_note(lv)
    cards.append(f'<section class="card" id="f{lv}"><header><span class="z">{zl(lv)}</span><h3>{E(NAMES[lv])}</h3></header>'
      f'<div class="cols"><div>{pl}</div><div class="side">'
      +(f'<h4>Connections</h4><ul class="conn">{"".join(conn)}</ul>' if conn else '<h4>Connections</h4><p class="sub">None found.</p>')
      +(f'<h4>Labels on this floor</h4><ol class="poi">{"".join(pl_list)}</ol>' if pl_list else '')
      +note+'</div></div></section>')
# summary table
rows=[]
for lv in ORDER:
    ups=sorted({g['hi'] for g in byl.get(lv,[]) if g['lo']==lv},reverse=True)
    dns=sorted({g['lo'] for g in byl.get(lv,[]) if g['hi']==lv},reverse=True)
    pl=[short(p['t']) for p in pois.get(lv,[]) if not p['t'].startswith('to #')]
    rows.append(f'<tr><td><a href="#f{lv}"><b>{zl(lv)}</b></a></td><td>{E(NAMES[lv])}</td><td>{", ".join(zl(u) for u in ups) or "–"}</td><td>{", ".join(zl(d) for d in dns) or "–"}</td></tr>')
CSS="""
.ctl{display:flex;gap:10px;flex-wrap:wrap;align-items:end;margin:10px 0 12px}.ctl label{display:flex;flex-direction:column;font-size:12px;color:var(--mut);gap:3px;flex:1;min-width:230px}
.ctl select,.ctl button{font:inherit;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg)}.ctl button{cursor:pointer}.ctl button:hover{border-color:var(--acc)}
.dgrid{display:grid;grid-template-columns:minmax(0,740px) minmax(260px,1fr);gap:16px;align-items:start}@media(max-width:1000px){.dgrid{grid-template-columns:1fr}}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;position:sticky;top:12px;font-size:14px}
.route{margin:6px 0 0;padding-left:20px}.route li{margin:7px 0}.route li.done{color:var(--mut)}.dir{color:var(--acc)}
.edge{transition:opacity .15s}.edge path{transition:stroke-width .15s}.bx{cursor:pointer;transition:opacity .15s}
.diag.active .edge{opacity:.13;filter:grayscale(1)}.diag.active .edge.on{opacity:1;filter:none}.diag.active .edge.on path{stroke-width:3.6}
.diag.active .bx{opacity:.4}.diag.active .bx.on{opacity:1}
.bx:hover .box{stroke:var(--acc)}.bx.src .box{stroke:#16a34a;stroke-width:3}.bx.dst .box{stroke:#dc2626;stroke-width:3}.bx.pick .box{stroke:var(--acc);stroke-width:2.4}
.bx.on .box{fill:color-mix(in srgb,var(--card) 80%,var(--acc) 20%)}
.rc rect{fill:var(--card);stroke:var(--line);transition:fill .1s}.rc text{font:11.5px system-ui;fill:var(--fg);pointer-events:none}.rc:hover rect{stroke:var(--acc)}
.rc.src rect{fill:#16a34a;stroke:#16a34a}.rc.dst rect{fill:#dc2626;stroke:#dc2626}.rc.src text,.rc.dst text{fill:#fff;font-weight:700}
.tag rect{rx:4}.tag.a rect{fill:#16a34a}.tag.b rect{fill:#dc2626}.tag text{font:700 10px system-ui;fill:#fff;text-anchor:middle}
.xp rect{fill:#111;rx:9}.xp text{font:700 10.5px system-ui;fill:#fff;text-anchor:middle}
@media(prefers-color-scheme:dark){.xp rect{fill:#f5f0e4}.xp text{fill:#111}}

:root{--bg:#fbfaf7;--fg:#1d1b16;--mut:#6b665a;--card:#fff;--line:#e4dfd2;--acc:#c2410c;--wall:#2b2a26;--ter:#94a3b8;--stair:#ea580c;--poi:#1d4ed8}
@media(prefers-color-scheme:dark){:root{--bg:#161512;--fg:#ece8dc;--mut:#a39d8d;--card:#1f1d19;--line:#34312a;--acc:#fb923c;--wall:#d8d3c3;--ter:#64748b;--stair:#fb923c;--poi:#60a5fa}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
.wrap{max-width:1120px;margin:0 auto;padding:28px 18px 60px}h1{font-size:28px;margin:0 0 4px}h2{margin:38px 0 10px;font-size:20px}h3{margin:0;font-size:17px}h4{margin:14px 0 6px;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut)}
.lead{color:var(--mut);margin:0 0 18px;max-width:760px}.sub{color:var(--mut);font-size:12.5px}
table{border-collapse:collapse;width:100%;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}th,td{padding:7px 12px;text-align:left;border-bottom:1px solid var(--line);font-size:14px}th{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut)}a{color:var(--acc)}
.diagwrap{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;overflow-x:auto}
.diag{width:100%;min-width:640px;height:auto}.box{fill:var(--bg);stroke:var(--line);stroke-width:1.2}.box.faint{stroke-dasharray:4 3}
.zt{font:700 15px ui-monospace,Menlo,monospace;fill:var(--acc)}.nt{font:600 14px system-ui;fill:var(--fg)}.st{font:12px system-ui;fill:var(--mut)}.pill{font:700 10px system-ui;fill:#fff}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin:16px 0}.card header{display:flex;align-items:baseline;gap:12px;margin-bottom:10px}
.z{font:700 15px ui-monospace,Menlo,monospace;background:var(--acc);color:#fff;padding:2px 9px;border-radius:6px}
.cols{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:20px}@media(max-width:820px){.cols{grid-template-columns:1fr}}
.plan{width:100%;height:auto;background:var(--bg);border:1px solid var(--line);border-radius:8px}.wall{stroke:var(--wall);stroke-width:1.3;stroke-linecap:round}.ter{stroke:var(--ter);stroke-width:1}.stair{stroke:var(--stair);stroke-width:1.2}
.pillg rect{fill:var(--stair)}.pillg text{font:700 10px system-ui;fill:#fff}.poig circle{fill:var(--poi);stroke:var(--bg);stroke-width:1.5}.poig text{font:700 9px system-ui;fill:#fff}
ul.conn,ol.poi{margin:0;padding:0;list-style:none}ul.conn li{margin:0 0 9px}.chip{display:inline-block;background:var(--stair);color:#fff;font:700 11px system-ui;padding:1px 7px;border-radius:9px}
ol.poi li{margin:2px 0;font-size:13.5px}.num{display:inline-block;width:18px;height:18px;border-radius:9px;background:var(--poi);color:#fff;font:700 10px/18px system-ui;text-align:center;margin-right:7px}.loc{color:var(--mut);font-size:11.5px}
.note{font-size:13px;color:var(--mut);background:var(--bg);border-left:3px solid var(--acc);padding:6px 10px;margin:12px 0 0}code{font:12.5px ui-monospace,Menlo,monospace;background:var(--bg);padding:1px 5px;border-radius:4px;border:1px solid var(--line)}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:var(--mut);margin:8px 0 0}.legend i{display:inline-block;width:22px;height:0;border-top:3px solid;vertical-align:middle;margin-right:6px}
"""
JS='\nconst FL=%FL%,RM=%RM%,ANCH=%ANCH%,BOX=%BOX%,X1=%X1%;\nconst GL={N:\'↑\',NE:\'↗\',E:\'→\',SE:\'↘\',S:\'↓\',SW:\'↙\',W:\'←\',NW:\'↖\'};\nlet A=null,B=null,ROUTES=null,loadErr=false;\nconst $=q=>document.querySelector(q),svg=$(\'svg.diag\'),panel=$(\'#panel\'),selA=$(\'#selA\'),selB=$(\'#selB\');\nconst NS=\'http://www.w3.org/2000/svg\';\nconst zl=z=>z>0?\'+\'+z:String(z);\nconst flName={};FL.forEach(f=>flName[f[0]]=f[1]);\nconst rmById={};RM.forEach(r=>rmById[r[0]]=r);\nfunction lvOf(c){return c[0]===\'F\'?+c.slice(1):rmById[+c.slice(1)][2]}\nfunction label(c){return c[0]===\'F\'?zl(+c.slice(1))+\' \'+flName[+c.slice(1)]+\' (floor)\':rmById[+c.slice(1)][1]}\nfunction fill(sel){sel.innerHTML=\'<option value="">–</option>\';\n FL.forEach(f=>{const g=document.createElement(\'optgroup\');g.label=zl(f[0])+\' \'+f[1];\n  const o=document.createElement(\'option\');o.value=\'F\'+f[0];o.textContent=\'Anywhere on this floor\';g.appendChild(o);\n  RM.filter(r=>r[2]===f[0]).forEach(r=>{const o=document.createElement(\'option\');o.value=\'R\'+r[0];o.textContent=r[1];g.appendChild(o)});\n  sel.appendChild(g)})}\nfill(selA);fill(selB);\nfunction pick(c){ if(A===null||(A!==null&&B!==null)){A=c;B=null}else if(c!==A){B=c} render() }\nsvg.addEventListener(\'click\',e=>{const rc=e.target.closest(\'.rc\'),bx=e.target.closest(\'.bx\');\n if(rc){pick(\'R\'+rc.dataset.r);return} if(bx){pick(\'F\'+bx.dataset.lv)}});\nselA.onchange=()=>{A=selA.value||null;if(A&&A===B)B=null;render()};\nselB.onchange=()=>{B=selB.value||null;if(B&&B===A)A=null;render()};\n$(\'#swap\').onclick=()=>{[A,B]=[B,A];render()};\n$(\'#clr\').onclick=()=>{A=B=null;render()};\nfunction tag(lv,txt,cls,off){const g=document.createElementNS(NS,\'g\');g.setAttribute(\'class\',\'tag \'+cls);\n const b=BOX[lv],y=b.y+b.h/2-8+off;g.innerHTML=`<rect x="2" y="${y}" width="40" height="16"/><text x="22" y="${y+11.5}">${txt}</text>`;svg.appendChild(g)}\nfunction render(){\n selA.value=A||\'\';selB.value=B||\'\';\n svg.querySelectorAll(\'.tag,.xp\').forEach(e=>e.remove());\n svg.querySelectorAll(\'.on,.src,.dst,.pick\').forEach(e=>e.classList.remove(\'on\',\'src\',\'dst\',\'pick\'));\n svg.classList.remove(\'active\');\n const boxes={};svg.querySelectorAll(\'.bx\').forEach(b=>boxes[b.dataset.lv]=b);\n const rcs={};svg.querySelectorAll(\'.rc\').forEach(r=>rcs[\'R\'+r.dataset.r]=r);\n if(A&&rcs[A])rcs[A].classList.add(\'src\'); if(B&&rcs[B])rcs[B].classList.add(\'dst\');\n if(A){const bx=boxes[lvOf(A)];bx.classList.add(B?\'src\':\'pick\');tag(lvOf(A),\'FROM\',\'a\',(B&&lvOf(B)===lvOf(A))?-10:0)}\n if(B){boxes[lvOf(B)].classList.add(\'dst\');tag(lvOf(B),\'TO\',\'b\',(A&&lvOf(A)===lvOf(B))?10:0)}\n if(!A){panel.innerHTML=\'<p class="sub">Pick a start (click a floor or room in the diagram, or use the menus).</p>\';return}\n if(!B){panel.innerHTML=`<p><b>From:</b> ${label(A)}</p><p class="sub">Now pick a destination.</p>`;return}\n if(!ROUTES){panel.innerHTML=loadErr?\'<p class="sub">Route data didn’t load, so I can’t show the route.</p>\':\'<p class="sub">Loading routes…</p>\';return}\n const d=ROUTES[A+\'|\'+B];\n const head=`<p style="margin:0 0 4px"><b style="color:#16a34a">${label(A)}</b> → <b style="color:#dc2626">${label(B)}</b></p>`;\n if(!d){panel.innerHTML=head+\'<p class="sub">No walking route between these on the map. The Teleport and pit are cut off from the tower, and the +468 platform has no stairs.</p>\';return}\n svg.classList.add(\'active\');\n const fl=new Set(d.f);fl.forEach(l=>boxes[l]&&boxes[l].classList.add(\'on\'));\n d.s.forEach(s=>{const e=$(\'#e-\'+s.id);if(e)e.classList.add(\'on\');\n  if(s.exit){const y=ANCH[s.id+\'@\'+s.fr];if(y===undefined)return;const g=document.createElementNS(NS,\'g\');g.setAttribute(\'class\',\'xp\');\n   g.innerHTML=`<rect x="${X1-94}" y="${y-9}" width="86" height="18"/><text x="${X1-51}" y="${y+4}">leave ${GL[s.exit]||\'\'} ${s.exit}</text>`;svg.appendChild(g)}});\n panel.innerHTML=head+d.h;\n}\nfetch(\'routes.json\').then(r=>r.json()).then(j=>{ROUTES=j;render()}).catch(()=>{loadErr=true;render()});\nrender();\n'
JS=(JS.replace('%FL%',json.dumps([[lv,NAMES[lv]] for lv in ORDER if lv not in Z.SKY_LEVELS])).replace('%RM%',json.dumps([[r_['id'],r_['name'],r_['lv']] for r_ in R.ROOMS])).replace('%ANCH%',json.dumps(ANCH)).replace('%BOX%',json.dumps({str(k):v for k,v in BOX.items()})).replace('%X1%',str(x0+boxw)))
page=f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(Z.TITLE)}</title><style>{CSS}</style></head><body><div class="wrap">
<h1>{E(Z.TITLE)}</h1>
<p class="lead">{Z.intro(len(st))}</p>
<h2>What connects to what</h2>
<p class="sub">Click a floor box (or a room inside it) to set the <b style="color:#16a34a">start</b>, then click another for the <b style="color:#dc2626">destination</b>. The stairs you need light up, everything else fades, and the steps appear alongside. A third click starts over.</p>
<div class="ctl"><label>From<select id="selA"></select></label><button id="swap" title="Swap start and destination">⇄ Swap</button><label>To<select id="selB"></select></label><button id="clr">Clear</button></div>
<div class="dgrid"><div class="diagwrap">{diagram}</div><aside class="panel" id="panel"><p class="sub">Pick a start and a destination to see the route here.</p></aside></div>
<p class="sub">Heights are map Z values, top is highest. Each numbered circle is a staircase or ramp (S1–S{len(st)}); its line runs between the two floors it joins. Dashed boxes are minor landings. Black “leave” badges on the highlighted route show which way to head out of that floor toward the next stairs.</p>
<h2>Floors at a glance</h2>
<table><tr><th>Height</th><th>Floor</th><th>Stairs up to</th><th>Stairs down to</th></tr>{"".join(rows)}</table>
<h2>Floor by floor</h2>
<div class="legend"><span><i style="border-color:var(--wall)"></i>walls</span><span><i style="border-color:var(--stair)"></i>stairs / ramps (S#)</span><span><i style="border-color:var(--ter)"></i>cave slopes</span><span><b style="color:var(--poi)">●</b> numbered labels</span></div>
{"".join(cards)}
<h2>Notes on reading this</h2>
<p class="sub"><b>Coordinates.</b> Plans are drawn in raw map-file orientation. To use a position in game, a map point (x, y) corresponds to in-game <code>/loc</code> Y, X = (−y, −x), and every “/loc” above is already converted. This hasn’t been verified in the client, so spot-check one stair with <code>/loc</code> before trusting the orientation.</p>
<p class="sub"><b>How I decoded it.</b> Each <code>L</code> line is a wall segment <code>x1,y1,z1,x2,y2,z2,r,g,b</code>; each <code>P</code> line is a label <code>x,y,z,r,g,b,size,text</code>. Floors are groups of flat segments at the same Z. A stair is a bundle of sloped segments joining two floors. <code>_1</code> holds the in-zone labels. <code>_2</code> holds the key (ground-spawn and Hunter placeholder legend), drawn far outside the zone at x up to 2030, so I excluded it from the plans.</p>
<p class="sub"><b>What the file can’t tell you.</b> It has no doors, zone lines, teleport destinations or elevator logic. {Z.LIMITS_NOTE}</p>
<p class="sub">{Z.SOURCE_NOTE}</p>
</div><script>{JS}</script></body></html>"""
open(os.path.join(OUT_DIR,'index.html'),'w').write(page)
print(len(page),len(st),len(lanes))
