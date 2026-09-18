// lx-polish client enhancements — orbs, stat pills, icons, reveal
(() => {
  if (window.__lxPolish) return; window.__lxPolish = true;
  const main = document.querySelector('main');
  if (main && !main.querySelector('.lx-orbs')) {
    const d = document.createElement('div'); d.className='lx-orbs'; d.setAttribute('aria-hidden','true'); main.prepend(d);
  }
  const proof = document.querySelector('p.proof');
  if (proof && !proof.classList.contains('lx-proof')) {
    const parts = proof.textContent.split('·').map(s=>s.trim()).filter(Boolean);
    proof.classList.add('lx-proof'); proof.innerHTML='';
    parts.forEach(t => {
      const s=document.createElement('span'); s.className='lx-stat';
      s.innerHTML=t.replace(/([0-9][0-9,]*)/g,'<b>$1</b>'); proof.appendChild(s);
    });
  }
  const icons=['🚀','🏆','🔎'];
  document.querySelectorAll('ul.personas li').forEach((li,i)=>{
    if(!li.querySelector('.lx-ico')){
      const s=document.createElement('span'); s.className='lx-ico'; s.textContent=icons[i%3];
      s.style.cssText='font-size:26px;display:block;margin-bottom:8px';
      li.querySelector('a')?.prepend(s);
    }
  });
  const els=document.querySelectorAll('ul.personas li, section.zone, .card-grid .card');
  els.forEach(e=>e.classList.add('lx-reveal'));
  if('IntersectionObserver' in window){
    const io=new IntersectionObserver(es=>es.forEach(e=>{ if(e.isIntersecting){ e.target.classList.add('lx-in'); io.unobserve(e.target);} }),{threshold:.08});
    els.forEach(e=>io.observe(e));
  } else els.forEach(e=>e.classList.add('lx-in'));
})();
