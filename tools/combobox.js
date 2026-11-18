/* Type-ahead picker that sits on top of a (hidden) <select>.
   makeCombo(select, entries, {labelFor, placeholder})
   entries: [{text, sub, kind, code, note}]  - choosing one sets select.value = code and fires 'change'.
   Returns {sync(), picked} - call sync() after the select changes by other means. */
function makeCombo(sel,entries,opts){
  opts=opts||{};
  sel.style.display='none';
  const wrap=document.createElement('div');wrap.className='cb';
  const inp=document.createElement('input');
  inp.type='text';inp.className='cbi';inp.placeholder=opts.placeholder||'Type to search…';
  inp.autocomplete='off';inp.spellcheck=false;
  inp.setAttribute('role','combobox');inp.setAttribute('aria-autocomplete','list');inp.setAttribute('aria-expanded','false');
  const ul=document.createElement('ul');ul.className='cbl';ul.setAttribute('role','listbox');ul.hidden=true;
  wrap.appendChild(inp);wrap.appendChild(ul);sel.parentNode.insertBefore(wrap,sel.nextSibling);
  const self={picked:null};
  let shown=[],hi=-1;
  const norm=s=>String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'');
  const idx=entries.map(e=>({e:e,n:norm(e.text),s:norm((e.sub||'')+' '+(e.kind||''))}));
  const KRANK={floor:0,room:1};
  function score(it,toks){
    let sc=0;
    for(const t of toks){
      const i=it.n.indexOf(t);
      if(i<0){ if(it.s.indexOf(t)<0) return -1; sc+=1; continue; }
      sc+= i===0?100 : (/[a-z0-9]/.test(it.n[i-1])?30:60);
    }
    return sc;
  }
  function search(q){
    const toks=norm(q).split(/[\s,]+/).filter(Boolean);
    if(!toks.length) return idx.filter(it=>it.e.kind==='floor'||it.e.kind==='room').map(it=>it.e);
    const r=[];
    idx.forEach((it,i)=>{const sc=score(it,toks);if(sc>=0)r.push({e:it.e,sc:sc,i:i})});
    r.sort((a,b)=>b.sc-a.sc||(KRANK[a.e.kind]===undefined?2:KRANK[a.e.kind])-(KRANK[b.e.kind]===undefined?2:KRANK[b.e.kind])||a.i-b.i);
    return r.slice(0,14).map(x=>x.e);
  }
  function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
  function draw(){
    ul.innerHTML='';
    if(!shown.length){ul.innerHTML='<li class="none">No matches</li>';return}
    shown.forEach((e,i)=>{
      const li=document.createElement('li');li.setAttribute('role','option');
      li.className=i===hi?'hi':'';
      li.innerHTML='<span class="t">'+esc(e.text)+'</span><span class="s">'+esc(e.sub||'')+'</span><span class="k">'+esc(e.kind||'')+'</span>';
      li.addEventListener('mousedown',ev=>{ev.preventDefault();choose(e)});
      ul.appendChild(li);
    });
    const cur=ul.children[hi];if(cur&&cur.scrollIntoView)cur.scrollIntoView({block:'nearest'});
  }
  function open(q){shown=search(q);hi=shown.length?0:-1;ul.hidden=false;inp.setAttribute('aria-expanded','true');draw()}
  function close(){ul.hidden=true;inp.setAttribute('aria-expanded','false')}
  function choose(e){
    self.picked={code:e.code,text:e.text,note:e.note||''};
    sel.value=e.code;close();
    sel.dispatchEvent(new Event('change'));
    self.sync();inp.blur();
  }
  self.sync=function(){
    const p=self.picked;
    const t=(p&&p.code===sel.value)?p.text:(sel.value?(opts.labelFor?opts.labelFor(sel.value):sel.value):'');
    if(document.activeElement!==inp)inp.value=t;
  };
  inp.addEventListener('focus',()=>{inp.select();open('')});
  inp.addEventListener('input',()=>open(inp.value));
  inp.addEventListener('keydown',ev=>{
    if(ev.key==='ArrowDown'){ev.preventDefault();if(ul.hidden)open(inp.value);else{hi=Math.min(shown.length-1,hi+1);draw()}}
    else if(ev.key==='ArrowUp'){ev.preventDefault();hi=Math.max(0,hi-1);draw()}
    else if(ev.key==='Enter'){ev.preventDefault();if(!ul.hidden&&shown[hi])choose(shown[hi])}
    else if(ev.key==='Escape'){close();inp.blur()}
  });
  inp.addEventListener('blur',()=>{
    close();
    if(inp.value.trim()===''&&sel.value){self.picked=null;sel.value='';sel.dispatchEvent(new Event('change'))}
    self.sync();
  });
  return self;
}
