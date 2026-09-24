(()=>{const p=location.pathname;const active=(href)=>p.endsWith(href)||p===href;const group=(label,items)=>`<details open><summary>${label}</summary><div class="tree-children">${items.map(([t,h])=>`<a class="${active(h)?'active':''}" href="${h}">${t}</a>`).join('')}</div></details>`;const html=`
<button class="tree-toggle" aria-label="Apri menu" aria-expanded="false"><span></span><span></span><span></span></button>
<div class="tree-overlay"></div>
<aside class="tree-sidebar" aria-label="Navigazione progetto">
  <div class="tree-brand"><a href="/"><strong>MultiCNC</strong><span>/ ENGINEERING</span></a><small>Precision modular platform</small></div>
  <nav class="tree-nav">
    <a class="tree-home ${active('/')||p==='/index.html'?'active':''}" href="/">Overview</a>
    ${group('01 · Core',['Master Spec','/docs/master-spec.html']?[['Master Spec','/docs/master-spec.html'],['Architecture','/docs/architecture.html'],['Decision Log','/docs/decisions.html']]:[])}
    ${group('02 · BOM',[['Base Precision','/bom/base.html'],['PCB Precision Kit','/bom/pcb-kit.html']])}
    ${group('03 · Mechanics',[['Automatic ToolDock','/mechanics/tooldock.html']])}
    ${group('04 · Modules',[['PCB','/bom/pcb-kit.html'],['Aluminium','/#aluminium'],['Thermoforming','/#thermoforming'],['Diode Laser','/#diode'],['Fiber MOPA','/#fiber'],['Knife','/#knife'],['Dispenser','/#dispenser'],['Vision','/#vision']])}
  </nav>
  <div class="tree-meta"><span>V0.2</span><span>2026-09-24</span></div>
</aside>`;document.body.insertAdjacentHTML('afterbegin',html);document.body.classList.add('with-tree');const btn=document.querySelector('.tree-toggle'),side=document.querySelector('.tree-sidebar'),ov=document.querySelector('.tree-overlay');const set=(open)=>{document.body.classList.toggle('tree-open',open);btn.setAttribute('aria-expanded',open?'true':'false')};btn.addEventListener('click',()=>set(!document.body.classList.contains('tree-open')));ov.addEventListener('click',()=>set(false));side.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{if(innerWidth<=820)set(false)}));addEventListener('keydown',e=>{if(e.key==='Escape')set(false)});})();