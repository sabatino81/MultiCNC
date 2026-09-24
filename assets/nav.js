(()=> {
  const p=location.pathname;
  const active=(href)=>href==='/' ? (p==='/'||p==='/index.html') : p===href || p.endsWith(href);
  const group=(label,items,prefixes=[])=>{
    const isOpen=items.some(([,h])=>active(h)) || prefixes.some(x=>p.startsWith(x));
    return `<details ${isOpen?'open':''}><summary>${label}</summary><div class="tree-children">${items.map(([t,h,b])=>`<a class="${active(h)?'active':''}" href="${h}"><span>${t}</span>${b?`<em>${b}</em>`:''}</a>`).join('')}</div></details>`;
  };
  const html=`
  <button class="tree-toggle" aria-label="Apri menu" aria-expanded="false"><span></span><span></span><span></span></button>
  <div class="tree-overlay"></div>
  <aside class="tree-sidebar" aria-label="Navigazione progetto">
    <div class="tree-brand"><a href="/"><strong>MultiCNC</strong><span>/ ENGINEERING</span></a><small>Precision modular manufacturing platform</small></div>
    <nav class="tree-nav">
      <a class="tree-home ${active('/')?'active':''}" href="/">Dashboard</a>

      ${group('01 · Progetto',[
        ['Overview','/general/index.html'],
        ['Visione & obiettivi','/general/vision.html'],
        ['Casi d’uso','/general/use-cases.html'],
        ['Requisiti qualitativi','/general/qualitative.html'],
        ['Requisiti quantitativi','/general/quantitative.html'],
        ['Standard & compliance','/general/standards.html'],
        ['Architettura generale','/general/architecture.html'],
        ['Filosofia modulare','/general/modularity.html'],
        ['Target prestazionali','/general/performance.html'],
        ['Vincoli di progetto','/general/constraints.html'],
        ['Glossario','/general/glossary.html'],
        ['Decision log','/docs/decisions.html']
      ],['/general/','/docs/decisions'])}

      ${group('02 · Base Precision',[
        ['Overview','/base/index.html'],
        ['Funzionalità','/base/functions.html'],
        ['Architettura meccanica','/base/mechanics.html'],
        ['Cinematica XYZ','/base/xyz.html'],
        ['Gantry Lift','/base/gantry-lift.html'],
        ['ToolDock','/mechanics/tooldock.html'],
        ['Elettronica & controllo','/base/control.html'],
        ['Sicurezza','/base/safety.html'],
        ['Interfacce moduli','/base/interfaces.html'],
        ['Target prestazionali','/base/performance.html'],
        ['Vincoli','/base/constraints.html'],
        ['BOM','/bom/base.html'],
        ['Test & validazione','/base/validation.html']
      ],['/base/','/bom/base','/mechanics/tooldock'])}

      ${group('03 · PCB Kit',[
        ['Overview','/pcb/index.html'],
        ['Funzionalità','/pcb/functions.html','NEXT'],
        ['Architettura','/pcb/architecture.html','NEXT'],
        ['Micro-spindle','/pcb/spindle.html','NEXT'],
        ['Vacuum pallet','/pcb/vacuum-pallet.html','NEXT'],
        ['Fiducial vision','/pcb/vision.html','NEXT'],
        ['Surface probing','/pcb/probing.html','NEXT'],
        ['Aspirazione','/pcb/extraction.html','NEXT'],
        ['Tooling & workflow','/pcb/workflow.html','NEXT'],
        ['Target & vincoli','/pcb/performance.html','NEXT'],
        ['BOM','/bom/pcb-kit.html'],
        ['Test & validazione','/pcb/validation.html','NEXT']
      ],['/pcb/','/bom/pcb-kit'])}

      ${group('04 · Aluminium Kit',[
        ['Overview','/modules/aluminium/index.html','PLANNED'],
        ['Rinforzi strutturali','/modules/aluminium/structure.html','PLANNED'],
        ['Spindle ATC','/modules/aluminium/atc.html','PLANNED'],
        ['Lubrificazione / MQL','/modules/aluminium/mql.html','PLANNED'],
        ['Chip management','/modules/aluminium/chips.html','PLANNED'],
        ['BOM','/modules/aluminium/bom.html','PLANNED']
      ],['/modules/aluminium/'])}

      ${group('05 · Thermoforming Kit',[
        ['Overview','/modules/thermoforming/index.html','PLANNED'],
        ['Heating','/modules/thermoforming/heating.html','PLANNED'],
        ['Vacuum & plenum','/modules/thermoforming/vacuum.html','PLANNED'],
        ['Cooling & process','/modules/thermoforming/process.html','PLANNED'],
        ['BOM','/modules/thermoforming/bom.html','PLANNED']
      ],['/modules/thermoforming/'])}

      ${group('06 · Diode Laser Kit',[
        ['Overview','/modules/diode/index.html','PLANNED'],
        ['Safety & extraction','/modules/diode/safety.html','PLANNED'],
        ['BOM','/modules/diode/bom.html','PLANNED']
      ],['/modules/diode/'])}

      ${group('07 · Fiber MOPA Kit',[
        ['Overview','/modules/fiber/index.html','PLANNED'],
        ['Galvo station','/modules/fiber/galvo.html','PLANNED'],
        ['Safety','/modules/fiber/safety.html','PLANNED'],
        ['BOM','/modules/fiber/bom.html','PLANNED']
      ],['/modules/fiber/'])}

      ${group('08 · Knife Kit',[
        ['Overview','/modules/knife/index.html','PLANNED'],
        ['Tangential / drag','/modules/knife/heads.html','PLANNED'],
        ['BOM','/modules/knife/bom.html','PLANNED']
      ],['/modules/knife/'])}

      ${group('09 · Dispenser Kit',[
        ['Overview','/modules/dispenser/index.html','PLANNED'],
        ['Pneumatica & valvole','/modules/dispenser/pneumatics.html','PLANNED'],
        ['BOM','/modules/dispenser/bom.html','PLANNED']
      ],['/modules/dispenser/'])}

      ${group('10 · Vision Kit',[
        ['Overview','/modules/vision/index.html','PLANNED'],
        ['Camera & ottiche','/modules/vision/camera.html','PLANNED'],
        ['Calibration','/modules/vision/calibration.html','PLANNED'],
        ['BOM','/modules/vision/bom.html','PLANNED']
      ],['/modules/vision/'])}

      ${group('11 · Software & Control',[
        ['Overview','/software/index.html','PLANNED'],
        ['LinuxCNC / Mesa','/software/motion.html','PLANNED'],
        ['ToolDock manager','/software/tooldock.html','PLANNED'],
        ['Calibration maps','/software/calibration.html','PLANNED'],
        ['Vision integration','/software/vision.html','PLANNED'],
        ['API / SDK','/software/api.html','PLANNED']
      ],['/software/'])}

      ${group('12 · Manufacturing',[
        ['Overview','/manufacturing/index.html','PLANNED'],
        ['CAD & drawings','/manufacturing/cad.html','PLANNED'],
        ['Assembly','/manufacturing/assembly.html','PLANNED'],
        ['Wiring','/manufacturing/wiring.html','PLANNED'],
        ['QA & metrology','/manufacturing/qa.html','PLANNED']
      ],['/manufacturing/'])}

      ${group('13 · Product',[
        ['Configurations','/product/configurations.html','PLANNED'],
        ['Module matrix','/product/module-matrix.html','PLANNED'],
        ['Cost & weight','/product/cost-weight.html','PLANNED'],
        ['Packaging & shipping','/product/shipping.html','PLANNED'],
        ['Serviceability','/product/serviceability.html','PLANNED']
      ],['/product/'])}
    </nav>
    <div class="tree-meta"><span>V0.3</span><span>STRUCTURE</span></div>
  </aside>`;
  document.body.insertAdjacentHTML('afterbegin',html);
  document.body.classList.add('with-tree');
  const btn=document.querySelector('.tree-toggle'), side=document.querySelector('.tree-sidebar'), ov=document.querySelector('.tree-overlay');
  const set=(open)=>{document.body.classList.toggle('tree-open',open);btn.setAttribute('aria-expanded',open?'true':'false')};
  btn.addEventListener('click',()=>set(!document.body.classList.contains('tree-open')));
  ov.addEventListener('click',()=>set(false));
  side.querySelectorAll('a').forEach(a=>a.addEventListener('click',e=>{const badge=a.querySelector('em');if(badge&&(badge.textContent==='PLANNED'||badge.textContent==='NEXT')){e.preventDefault();return;}if(innerWidth<=820)set(false)}));
  addEventListener('keydown',e=>{if(e.key==='Escape')set(false)});
})();