import os,sys,json,html
if __name__=='__main__' and len(sys.argv)>=4:
    os.environ.update(EQ_ZONE=sys.argv[1],EQ_MAP_DIR=sys.argv[2],EQ_OUT_DIR=sys.argv[3])
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from config import Z,OUT_DIR
import route as R
E=html.escape
ROOMS=R.ROOMS; ids=[r['id'] for r in ROOMS]
ORDER=sorted(ids,key=lambda i:(-ROOMS[i]['lv'] if False else 0))
# order rooms top floor to bottom, then name
order=sorted(ids,key=lambda i:(-ROOMS[i]['lv'],ROOMS[i]['name']))
def waycmd(x,y,z):
    """A copyable /way command; /way takes the same order as /loc prints: Y, X, Z."""
    return f'<code class="way" title="Click to copy, then paste in the chat window to set a waypoint">/way {round(-y)}, {round(-x)}, {round(z)}</code>'
def legs(l): return " → ".join("<b>%s</b> %d"%(h,d) for h,d in l) if l else "a few steps"
SUFFIX={}
def rtxt(a,b):
    r=R.route(a,b)
    if r is None: return None
    A=ROOMS[a]['name'];B=ROOMS[b]['name']
    out=[];first=None;up=dn=0
    firstwalk=True
    for s in r['steps']:
        if s['k']=='walk':
            if firstwalk:
                h=s['legs'][0][0] if s['legs'] else '–'; first=h
                head=(f"Leave <b>{E(A)}</b> heading <b class='dir'>{h}</b>" if s['legs'] else f"Leave <b>{E(A)}</b>")
                firstwalk=False
            else: head="Then head"
            if s['toR']:
                tail=f"to <b>{E(B)}</b>"+(" <span class='sub'>(its outline is closed on the map: walk up to its walls and look for the door)</span>" if s['sealed'] else "")
            else:
                sid=s['to'].split()[1]; tail=f"to the <span class='chip'>{sid}</span> link <span class='sub'>({waycmd(s['xy'][0],s['xy'][1],s['lv'])})</span>"
            out.append(f"<li>{head}: {legs(s['legs'])} {tail}</li>")
        elif s['k']=='portal':
            out.append(f"<li><span class='chip'>{s['id']}</span> ✦ use the <b>teleport</b> to <b>{R.zl(s['to'])}</b> ({E(s['toname'])})</li>")
        else:
            if s['dir']=='up': up+=1
            else: dn+=1
            arrow='▲ up' if s['dir']=='up' else '▼ down'
            out.append(f"<li><span class='chip'>{s['id']}</span> {arrow} to <b>{R.zl(s['to'])}</b> ({E(s['toname'])})</li>")
    out.append(f"<li class='done'>Arrive at <b>{E(B)}</b> · about {int(round(r['dist'],-1))} units total</li>")
    if first is None: first='–'
    return dict(html="<ol class='route'>"+"".join(out)+"</ol>",h=first,up=up,dn=dn,d=r['dist'])
data={}
for a in ids:
    for b in ids:
        if a==b: continue
        data["%d_%d"%(a,b)]=rtxt(a,b)
# matrix
def bucket(d): return 0 if d<250 else 1 if d<600 else 2 if d<1000 else 3
th="".join(f"<th class='col' title='{E(ROOMS[b]['name'])}'><div>{E(ROOMS[b]['name'])}</div></th>" for b in order)
rows=[]
for a in order:
    tds=[f"<th class='row'>{E(ROOMS[a]['name'])}<span class='z'>{R.zl(ROOMS[a]['lv'])}</span></th>"]
    for b in order:
        if a==b: tds.append("<td class='self'>·</td>"); continue
        d=data["%d_%d"%(a,b)]
        if d is None: tds.append(f"<td class='nw' data-k='{a}_{b}'>?</td>"); continue
        v=(f"▲{d['up']}" if d['up'] else "")+(f"▼{d['dn']}" if d['dn'] else "")
        tds.append(f"<td class='c b{bucket(d['d'])}' data-k='{a}_{b}'><b>{d['h']}</b><i>{v}</i></td>")
    rows.append("<tr>"+"".join(tds)+"</tr>")
matrix=f"<div class='mwrap'><table class='mx'><tr><th></th>{th}</tr>{''.join(rows)}</table></div>"
# per-room sheets
sheets=[]
for a in order:
    li=[]
    for b in order:
        if a==b: continue
        d=data["%d_%d"%(a,b)]
        if d is None: li.append(f"<li><b>{E(ROOMS[b]['name'])}</b> <span class='sub'>no walking route in the map (teleport)</span></li>"); continue
        li.append(f"<li><button class='lk' data-k='{a}_{b}'><b>{E(ROOMS[b]['name'])}</b> <span class='z'>{R.zl(ROOMS[b]['lv'])}</span></button><span class='h'>leave <b class='dir'>{d['h']}</b></span><span class='sub'>{('▲%d '%d['up'] if d['up'] else '')}{('▼%d'%d['dn'] if d['dn'] else '')}</span></li>")
    sheets.append(f"<details><summary><b>From {E(ROOMS[a]['name'])}</b> <span class='z'>{R.zl(ROOMS[a]['lv'])}</span></summary><ul class='sheet'>{''.join(li)}</ul></details>")
# stair key
key=[]
for g in R.STAIRS:
    f=" ".join(waycmd(p[0],p[1],g['lo']) for p in g['feet']); h=" ".join(waycmd(p[0],p[1],g['hi']) for p in g['heads'])
    key.append(f"<tr><td><span class='chip'>{g['id']}</span></td><td>{R.zl(g['lo'])} {E(R.NAMES[g['lo']])}</td><td>{R.zl(g['hi'])} {E(R.NAMES[g['hi']])}</td><td class='sub'>{f}</td><td class='sub'>{h}</td></tr>")
CSS="""
.way{font:12.5px ui-monospace,Menlo,Consolas,monospace;background:var(--bg);border:1px solid var(--line);border-radius:5px;padding:0 5px;cursor:copy;white-space:nowrap;color:var(--fg)}.way:hover{border-color:var(--acc)}.way.copied{background:var(--acc);color:#fff}
:root{--bg:#fbfaf7;--fg:#1d1b16;--mut:#6b665a;--card:#fff;--line:#e4dfd2;--acc:#c2410c}
@media(prefers-color-scheme:dark){:root{--bg:#161512;--fg:#ece8dc;--mut:#a39d8d;--card:#1f1d19;--line:#34312a;--acc:#fb923c}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:26px 16px 60px}h1{font-size:27px;margin:0 0 4px}h2{margin:34px 0 10px;font-size:19px}.lead,.sub{color:var(--mut)}.sub{font-size:12.5px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.pick{display:flex;gap:10px;flex-wrap:wrap;align-items:end}.pick label{display:flex;flex-direction:column;font-size:12px;color:var(--mut);gap:3px;flex:1;min-width:220px}
select,button{font:inherit;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--fg)}button{cursor:pointer}
.route{margin:14px 0 0;padding-left:22px}.route li{margin:7px 0}.route li.done{color:var(--mut)}
.chip{display:inline-block;background:var(--acc);color:#fff;font:700 11px system-ui;padding:1px 7px;border-radius:9px}
.dir{color:var(--acc);font-size:1.05em}
.mwrap{overflow:auto;border:1px solid var(--line);border-radius:10px;background:var(--card)}
.mx{border-collapse:separate;border-spacing:0;font-size:12px}.mx th,.mx td{border-right:1px solid var(--line);border-bottom:1px solid var(--line);padding:0}
.mx th.col{height:150px;min-width:36px;vertical-align:bottom;position:sticky;top:0;background:var(--card)}.mx th.col div{writing-mode:vertical-rl;transform:rotate(180deg);white-space:nowrap;padding:6px 4px;text-align:left;font-weight:600}
.mx th.row{position:sticky;left:0;background:var(--card);text-align:left;white-space:nowrap;padding:5px 10px;font-weight:600;z-index:1}
.z{font:700 10.5px ui-monospace,Menlo,monospace;color:var(--acc);margin-left:6px}
.mx td{min-width:36px;height:42px;text-align:center;cursor:pointer}.mx td b{display:block;font-size:13px}.mx td i{display:block;font-style:normal;font-size:9.5px;color:var(--mut)}
.mx td.self{background:repeating-linear-gradient(45deg,transparent 0 4px,var(--line) 4px 5px);cursor:default}.mx td.nw{color:var(--mut)}
.b0{background:rgba(34,197,94,.20)}.b1{background:rgba(234,179,8,.20)}.b2{background:rgba(249,115,22,.22)}.b3{background:rgba(239,68,68,.22)}.mx td.sel{outline:2px solid var(--acc);outline-offset:-2px}
details{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:8px 0;padding:8px 14px}summary{cursor:pointer;padding:4px 0}
ul.sheet{list-style:none;margin:8px 0 4px;padding:0;columns:2 340px}ul.sheet li{display:flex;gap:10px;align-items:baseline;padding:3px 0;break-inside:avoid}ul.sheet .h{margin-left:auto;font-size:13px}
.lk{border:0;background:none;padding:0;text-align:left;color:var(--fg)}.lk:hover{color:var(--acc)}
table.key{border-collapse:collapse;width:100%;background:var(--card);border:1px solid var(--line)}table.key th,table.key td{padding:6px 10px;border-bottom:1px solid var(--line);text-align:left;font-size:13px;vertical-align:top}table.key th{font-size:11.5px;text-transform:uppercase;color:var(--mut)}
.legend span{display:inline-block;padding:1px 8px;border-radius:5px;margin-right:6px;font-size:12px}
"""
_here=os.path.dirname(os.path.abspath(__file__))
CSS+=open(os.path.join(_here,'combobox.css')).read()
_ent=[dict(text=ROOMS[i]['name'],sub=R.zl(ROOMS[i]['lv']),kind="room",code=str(i)) for i in order]
for lp_ in R.label_points():
    if lp_['room'] is None or lp_['room'] not in order: continue
    rn=ROOMS[lp_['room']]['name']
    _ent.append(dict(text=lp_['text'],sub="in "+rn,kind=lp_['kind'],code=str(lp_['room']),note="<b>%s</b> is in <b>%s</b>."%(E(lp_['text']),E(rn))))
COMBO_JS=open(os.path.join(_here,'combobox.js')).read()
opts="".join(f"<option value='{i}'>{R.zl(ROOMS[i]['lv'])}  {E(ROOMS[i]['name'])}</option>" for i in order)
JS="""
const D=%s;
const f=document.getElementById('from'),t=document.getElementById('to'),out=document.getElementById('out');
function show(){const k=f.value+'_'+t.value;document.querySelectorAll('.mx td.sel').forEach(e=>e.classList.remove('sel'));
 const td=document.querySelector(`.mx td[data-k="${k}"]`);if(td)td.classList.add('sel');
 if(f.value===t.value){out.innerHTML='<p class="sub">Pick two different rooms.</p>';return}
 const d=D[k];out.innerHTML=d?d.html:'<p class="sub">The map has no walking connection between these two (the pit and teleport cross are cut off from the tower). Where the Teleport leads isn’t in the map file.</p>';}
f.onchange=t.onchange=show;
document.getElementById('swap').onclick=()=>{const a=f.value;f.value=t.value;t.value=a;show()};
document.addEventListener('click',e=>{const el=e.target.closest('[data-k]');if(!el)return;const [a,b]=el.dataset.k.split('_');f.value=a;t.value=b;show();document.getElementById('picker').scrollIntoView({behavior:'smooth',block:'start'})});
f.value=%d;t.value=%d;show();
document.addEventListener('click',e=>{const w=e.target.closest('.way');if(!w)return;e.stopPropagation();const t=w.textContent.trim();
 try{navigator.clipboard.writeText(t).then(()=>{const o=w.title;w.title='Copied!';w.classList.add('copied');setTimeout(()=>{w.title=o;w.classList.remove('copied')},1200)},()=>{})}catch(_){}},true);
""" % (json.dumps({k:(dict(html=v['html']) if v else None) for k,v in data.items()}),order[0],order[-3])
JS+=("""
const ENT=__ENT__;
__COMBO__
const lbl=v=>{const e=ENT.find(x=>x.kind==='room'&&x.code===v);return e?e.text:''};
const cf=makeCombo(f,ENT,{labelFor:lbl,placeholder:'Type a room or NPC…'}),ct=makeCombo(t,ENT,{labelFor:lbl,placeholder:'Type a room or NPC…'});
const _show=show;
show=function(){_show();cf.sync();ct.sync();
 const n=cb=>{const p=cb.picked;return(p&&p.code===(cb===cf?f:t).value&&p.note)?'<p class="sub">'+p.note+'</p>':''};
 out.insertAdjacentHTML('afterbegin',n(cf)+n(ct))};
f.onchange=t.onchange=show;
document.getElementById('swap').onclick=()=>{const a=f.value,p=cf.picked;f.value=t.value;t.value=a;cf.picked=ct.picked;ct.picked=p;show()};
show();
""").replace("__ENT__",json.dumps(_ent,ensure_ascii=False)).replace("__COMBO__",COMBO_JS)
page=f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(Z.ROUTES_TITLE)}</title><style>{CSS}</style></head><body><div class="wrap">
<h1>{E(Z.ROUTES_TITLE)}</h1>
<p class="lead">How to walk from any named room to any other, with the compass direction to head when you leave each room. Built from Brewall’s map; stair numbers (S1–S23) match the floors-and-connections page.</p>
<h2 id="picker">Route finder</h2>
<div class="card"><div class="pick"><label>From<select id="from">{opts}</select></label><button id="swap" title="Swap">⇄</button><label>To<select id="to">{opts}</select></label></div><div id="out"></div></div>
<h2>Matrix</h2>
<p class="sub">Rows are where you start, columns where you’re going. Each cell shows the direction to head out of the starting room, then ▲ up / ▼ down on the way. Tap a cell for the full route. Colour is rough distance: <span class="legend"><span class="b0">short</span><span class="b1">medium</span><span class="b2">long</span><span class="b3">very long</span></span></p>
{matrix}
<h2>Cheat sheet by starting room</h2>
<p class="sub">Open a room, then tap a destination for the full steps.</p>
{"".join(sheets)}
<h2>Stair key</h2>
<table class="key"><tr><th>Stair</th><th>Bottom</th><th>Top</th><th>Bottom end</th><th>Top end</th></tr>{"".join(key)}</table>
<h2>Notes</h2>
<p class="sub"><b>Directions.</b> N, E, S, W follow the in-game map, with north at the top of the map window. Numbers are approximate distances in map units, and each leg is simplified from the walkable corridors, so follow the corridor rather than a rigid straight line. Locations are <code>/way Y, X, Z</code> commands: click one to copy it, paste it into the chat window and EverQuest sets a waypoint. The conversion from the map file follows the community-documented format (map x = −second /loc number, map y = −first); it hasn’t been verified in the client, so stand on one stair and type <code>/loc</code> to check before trusting the compass.</p>
<p class="sub"><b>Limits.</b> Routes are the shortest walk computed from the wall outlines, assuming every gap in a wall is a doorway. The map has no doors, so a wall gap that’s really a barrier would break a route. {Z.ROUTES_LIMITS_NOTE}</p>
</div><script>{JS}</script></body></html>"""
open(os.path.join(OUT_DIR,'cheatsheet.html'),'w').write(page)
print(len(page),len(data),sum(1 for v in data.values() if v is None))
