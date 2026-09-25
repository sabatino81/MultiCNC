(()=> {
  const VERSION='V0.6';

  // Root of the docs site, derived from this script's own URL (assets/nav.js → ../).
  // Works from disk (file://), at a domain root and under a GitHub Pages subpath.
  const me=document.currentScript||document.querySelector('script[src$="nav.js"]');
  const ROOT=new URL('../',me.src);
  const url=(h)=>new URL(h.replace(/^\//,''),ROOT).href;
  const norm=(u)=>{const x=new URL(u,location.href);return (x.origin+x.pathname).replace(/index\.html$/,'')};
  const here=norm(location.href);
  const active=(h)=>norm(url(h))===here;
  const under=(prefix)=>here.startsWith(norm(url(prefix)));

  const TREE=[
    ['00','Business',[
      ['Overview','business/index.html'],
      ['Mercato & competitor','business/market.html'],
      ['Prezzo & margini','business/pricing.html'],
      ['Clienti & canali','business/channels.html','NEXT']
    ],['business/']],
    ['01','Progetto',[
      ['Overview','general/index.html'],
      ['Visione & obiettivi','general/vision.html'],
      ['Casi d’uso','general/use-cases.html'],
      ['Requisiti qualitativi','general/qualitative.html'],
      ['Requisiti quantitativi','general/quantitative.html'],
      ['Standard & compliance','general/standards.html'],
      ['Architettura generale','general/architecture.html'],
      ['Filosofia modulare','general/modularity.html'],
      ['Target prestazionali','general/performance.html'],
      ['Vincoli di progetto','general/constraints.html'],
      ['Glossario','general/glossary.html'],
      ['Master Spec','docs/master-spec.html'],
      ['System architecture','docs/architecture.html'],
      ['Decision log','docs/decisions.html']
    ],['general/','docs/']],
    ['02','Basi · Standard',[
      ['Overview','base/index.html'],
      ['Tre basi','base/lineup.html'],
      ['Interfacce comuni · ICD','base/icd.html'],
      ['Load case · D014','base/loads.html'],
      ['Funzionalità','base/functions.html'],
      ['Architettura meccanica','base/mechanics.html'],
      ['Cinematica XYZ','base/xyz.html'],
      ['Guide Standard · D015','base/rails.html'],
      ['CAD Standard · mule','base/cad-standard.html'],
      ['Rigidezza · D028','base/compliance-d028.html'],
      ['ToolDock e testa · D029','base/tooldock-d029.html'],
      ['FEA a solidi · D031','base/fea-d031.html'],
      ['Clearance & lift','base/gantry-lift.html'],
      ['ToolDock','mechanics/tooldock.html'],
      ['ToolDock meccanico · D016','base/tooldock-d016.html'],
      ['Elettronica & controllo','base/control.html'],
      ['Sicurezza','base/safety.html'],
      ['Interfacce moduli','base/interfaces.html'],
      ['Target prestazionali','base/performance.html'],
      ['Vincoli','base/constraints.html'],
      ['BOM Standard','bom/base.html'],
      ['BOM Light Core','bom/base-light.html'],
      ['BOM Platform Pack','bom/platform-pack.html'],
      ['BOM Pro','bom/base-pro.html'],
      ['Test & validazione','base/validation.html']
    ],['base/','bom/base','mechanics/']],
    ['03','PCB Kit',[
      ['Overview','pcb/index.html'],
      ['Funzionalità','pcb/functions.html','NEXT'],
      ['Architettura','pcb/architecture.html','NEXT'],
      ['Micro-spindle','pcb/spindle.html','NEXT'],
      ['Vacuum pallet','pcb/vacuum-pallet.html','NEXT'],
      ['Fiducial vision','pcb/vision.html','NEXT'],
      ['Surface probing','pcb/probing.html','NEXT'],
      ['Aspirazione','pcb/extraction.html','NEXT'],
      ['Tooling & workflow','pcb/workflow.html','NEXT'],
      ['Target & vincoli','pcb/performance.html','NEXT'],
      ['BOM','bom/pcb-kit.html'],
      ['Test & validazione','pcb/validation.html','NEXT']
    ],['pcb/','bom/pcb-kit']],
    ['04','Aluminium Kit',[
      ['Overview','modules/aluminium/index.html','PLANNED'],
      ['Rinforzi strutturali','modules/aluminium/structure.html','PLANNED'],
      ['Spindle ATC','modules/aluminium/atc.html','PLANNED'],
      ['Lubrificazione / MQL','modules/aluminium/mql.html','PLANNED'],
      ['Chip management','modules/aluminium/chips.html','PLANNED'],
      ['BOM','modules/aluminium/bom.html','PLANNED']
    ],['modules/aluminium/']],
    ['05','Thermoforming Kit',[
      ['Overview','modules/thermoforming/index.html','PLANNED'],
      ['Heating','modules/thermoforming/heating.html','PLANNED'],
      ['Vacuum & plenum','modules/thermoforming/vacuum.html','PLANNED'],
      ['Cooling & process','modules/thermoforming/process.html','PLANNED'],
      ['BOM','modules/thermoforming/bom.html','PLANNED']
    ],['modules/thermoforming/']],
    ['06','Diode Laser Kit',[
      ['Overview','modules/diode/index.html','PLANNED'],
      ['Safety & extraction','modules/diode/safety.html','PLANNED'],
      ['BOM','modules/diode/bom.html','PLANNED']
    ],['modules/diode/']],
    ['07','Fiber MOPA Kit',[
      ['Overview','modules/fiber/index.html','PLANNED'],
      ['Galvo station','modules/fiber/galvo.html','PLANNED'],
      ['Safety','modules/fiber/safety.html','PLANNED'],
      ['BOM','modules/fiber/bom.html','PLANNED']
    ],['modules/fiber/']],
    ['08','Knife Kit',[
      ['Overview','modules/knife/index.html','PLANNED'],
      ['Tangential / drag','modules/knife/heads.html','PLANNED'],
      ['BOM','modules/knife/bom.html','PLANNED']
    ],['modules/knife/']],
    ['09','Dispenser Kit',[
      ['Overview','modules/dispenser/index.html','PLANNED'],
      ['Pneumatica & valvole','modules/dispenser/pneumatics.html','PLANNED'],
      ['BOM','modules/dispenser/bom.html','PLANNED']
    ],['modules/dispenser/']],
    ['10','Vision Kit',[
      ['Overview','modules/vision/index.html','PLANNED'],
      ['Camera & ottiche','modules/vision/camera.html','PLANNED'],
      ['Calibration','modules/vision/calibration.html','PLANNED'],
      ['BOM','modules/vision/bom.html','PLANNED']
    ],['modules/vision/']],
    ['11','Software & Control',[
      ['Overview','software/index.html','PLANNED'],
      ['LinuxCNC / Mesa','software/motion.html','PLANNED'],
      ['ToolDock manager','software/tooldock.html','PLANNED'],
      ['Calibration maps','software/calibration.html','PLANNED'],
      ['Vision integration','software/vision.html','PLANNED'],
      ['API / SDK','software/api.html','PLANNED']
    ],['software/']],
    ['12','Manufacturing',[
      ['Overview','manufacturing/index.html','PLANNED'],
      ['CAD & drawings','manufacturing/cad.html','PLANNED'],
      ['Assembly','manufacturing/assembly.html','PLANNED'],
      ['Wiring','manufacturing/wiring.html','PLANNED'],
      ['QA & metrology','manufacturing/qa.html','PLANNED']
    ],['manufacturing/']],
    ['13','Product',[
      ['Configurations','product/configurations.html','PLANNED'],
      ['Module matrix','product/module-matrix.html','PLANNED'],
      ['Cost & weight','product/cost-weight.html','PLANNED'],
      ['Packaging & shipping','product/shipping.html','PLANNED'],
      ['Serviceability','product/serviceability.html','PLANNED']
    ],['product/']]
  ];
  window.MULTICNC={VERSION,TREE,url};

  const link=([t,h,b])=>b
    ? `<span class="tree-link is-${b.toLowerCase()}" aria-disabled="true"><span>${t}</span><em>${b}</em></span>`
    : `<a class="tree-link ${active(h)?'active':''}" href="${url(h)}"${active(h)?' aria-current="page"':''}><span>${t}</span></a>`;
  const group=([n,label,items,prefixes])=>{
    const ready=items.filter(i=>!i[2]).length;
    const open=items.some(([,h,b])=>!b&&active(h))||prefixes.some(under);
    const state=ready===items.length?'done':ready?'wip':'planned';
    return `<details class="tree-group is-${state}" ${open?'open':''}><summary><b>${n}</b><span>${label}</span><i title="${ready}/${items.length} capitoli pronti">${ready}/${items.length}</i></summary><div class="tree-children">${items.map(link).join('')}</div></details>`;
  };

  const html=`
  <div class="read-progress" aria-hidden="true"><span></span></div>
  <button class="tree-toggle" aria-label="Apri menu" aria-expanded="false"><span></span><span></span><span></span></button>
  <div class="tree-overlay"></div>
  <aside class="tree-sidebar" aria-label="Navigazione progetto">
    <div class="tree-brand"><a href="${url('index.html')}"><span class="logo" aria-hidden="true"><svg viewBox="0 0 32 32"><rect x="3" y="3" width="26" height="26" rx="7"/><path d="M9 22V10l7 7 7-7v12"/></svg></span><span><strong>MultiCNC</strong><small>Engineering · ${VERSION}</small></span></a></div>
    <label class="tree-search"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg><input type="search" placeholder="Cerca capitolo…" aria-label="Cerca capitolo"><kbd>/</kbd></label>
    <nav class="tree-nav">
      <a class="tree-home ${active('index.html')?'active':''}" href="${url('index.html')}"><span>Dashboard</span></a>
      ${TREE.map(group).join('')}
    </nav>
    <div class="tree-meta"><span><i class="dot"></i>${VERSION} · Architecture</span><span>2026</span></div>
  </aside>`;
  document.documentElement.classList.add('js');
  document.body.insertAdjacentHTML('afterbegin',html);
  document.body.classList.add('with-tree');

  const btn=document.querySelector('.tree-toggle'),ov=document.querySelector('.tree-overlay'),side=document.querySelector('.tree-sidebar');
  const set=(open)=>{document.body.classList.toggle('tree-open',open);btn.setAttribute('aria-expanded',open?'true':'false')};
  btn.addEventListener('click',()=>set(!document.body.classList.contains('tree-open')));
  ov.addEventListener('click',()=>set(false));
  side.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{if(innerWidth<=820)set(false)}));

  // Sidebar search
  const q=side.querySelector('.tree-search input');
  q.addEventListener('input',()=>{
    const s=q.value.trim().toLowerCase();
    side.querySelectorAll('.tree-group').forEach(g=>{
      let hit=false;
      g.querySelectorAll('.tree-link').forEach(l=>{const m=!s||l.textContent.toLowerCase().includes(s)||g.querySelector('summary').textContent.toLowerCase().includes(s);l.hidden=!m;hit=hit||m});
      g.hidden=!hit; if(s) g.open=hit;
    });
  });
  addEventListener('keydown',e=>{
    if(e.key==='Escape'){set(false);if(document.activeElement===q){q.value='';q.dispatchEvent(new Event('input'));q.blur()}}
    if(e.key==='/'&&!/input|textarea/i.test(document.activeElement.tagName)){e.preventDefault();if(innerWidth<=820)set(true);q.focus()}
  });

  // Keep the active item in view inside the sidebar
  const cur=side.querySelector('.tree-link.active');
  if(cur) cur.scrollIntoView({block:'center'});

  // Prev / next pager across the chapters that exist
  const flat=[['Dashboard','index.html'],...TREE.flatMap(g=>g[2].filter(i=>!i[2]))];
  const i=flat.findIndex(([,h])=>active(h));
  const main=document.querySelector('main');
  if(main&&i>=0){
    const prev=flat[i-1],next=flat[i+1];
    const card=(it,dir)=>it?`<a class="pager-${dir}" href="${url(it[1])}"><small>${dir==='prev'?'← Precedente':'Successivo →'}</small><strong>${it[0]}</strong></a>`:'<span></span>';
    main.insertAdjacentHTML('beforeend',`<nav class="pager" aria-label="Capitoli">${card(prev,'prev')}${card(next,'next')}</nav>`);
  }
  if(!document.querySelector('.footer')) document.body.insertAdjacentHTML('beforeend',`<footer class="shell footer"><span>MultiCNC · Engineering documentation · ${VERSION}</span><span>Valori <b class="status-target">TARGET</b> = obiettivi, non specifiche commerciali</span></footer>`);

  // Reading progress
  const bar=document.querySelector('.read-progress span');
  const onScroll=()=>{const h=document.documentElement;const p=h.scrollTop/Math.max(1,h.scrollHeight-h.clientHeight);bar.style.transform=`scaleX(${Math.min(1,p)})`};
  addEventListener('scroll',onScroll,{passive:true});onScroll();

  // Pointer spotlight on cards and panels
  document.addEventListener('pointermove',e=>{
    const el=e.target.closest&&e.target.closest('.card,.panel,.metric,.bom-kpi');
    if(!el)return;const r=el.getBoundingClientRect();
    el.style.setProperty('--mx',`${e.clientX-r.left}px`);el.style.setProperty('--my',`${e.clientY-r.top}px`);
  },{passive:true});

  // Reveal on scroll
  const items=document.querySelectorAll('main .pagehead, main .section, main .metric-grid, main .bom-summary, main .grid > *, main .callout, .hero-visual');
  if('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches){
    items.forEach((el,k)=>{el.classList.add('reveal');el.style.setProperty('--d',`${Math.min(k,8)*45}ms`)});
    const io=new IntersectionObserver(es=>es.forEach(en=>{if(en.isIntersecting){en.target.classList.add('in');io.unobserve(en.target)}}),{rootMargin:'0px 0px -6% 0px'});
    items.forEach(el=>io.observe(el));
  }
})();
