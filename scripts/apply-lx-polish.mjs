// scripts/apply-lx-polish.mjs
// Applies LLMS-Explorer punchy polish to source files.
// Usage: node scripts/apply-lx-polish.mjs [--root .] [--write]
import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
const ROOT = path.resolve(args.includes('--root') ? args[args.indexOf('--root')+1] : '.');
const WRITE = args.includes('--write');

const CSS = `/* lx-polish — punchy theme */
:root{ --lx1:#5b2cff; --lx2:#9d6bff; --lx3:#00d1b2; --lx4:#ff7a3d; --lx-dark:#17142b; }
body{
  background:
    radial-gradient(900px 420px at 12% -4%, rgba(109,92,255,.10), transparent 60%),
    radial-gradient(800px 380px at 88% 2%, rgba(0,194,168,.10), transparent 60%),
    var(--paper, #faf8f4);
}
.site-header{ position:sticky; top:0; z-index:60; backdrop-filter:blur(14px) saturate(1.2); background:color-mix(in srgb, var(--paper,#faf8f4) 82%, transparent); border-bottom:1px solid var(--line,#e4ddd0); }
.site-nav .brand{ font-weight:800; letter-spacing:-.02em; background:linear-gradient(90deg,var(--lx1),var(--lx3)); -webkit-background-clip:text; background-clip:text; color:transparent; -webkit-text-fill-color:transparent; }
main{ position:relative; max-width:1160px; margin-inline:auto; }
.lx-orbs{ position:absolute; inset:-20px 0 0 0; height:480px; pointer-events:none; overflow:hidden; z-index:0; }
.lx-orbs::before,.lx-orbs::after{ content:""; position:absolute; border-radius:50%; filter:blur(60px); opacity:.45; animation:lx-float 12s ease-in-out infinite alternate; }
.lx-orbs::before{ width:420px; height:420px; left:-120px; top:-80px; background:radial-gradient(circle,#a99bff,transparent 70%); }
.lx-orbs::after{ width:380px; height:380px; right:-100px; top:-40px; background:radial-gradient(circle,#7de8d3,transparent 70%); animation-delay:-6s; }
@keyframes lx-float{ to{ transform:translateY(26px) scale(1.06); } }
main > h1, main > .eyebrow, main > .lede, main > .hero-support, main > .hero-actions, main > .proof{ position:relative; z-index:1; }
main h1{
  font-size:clamp(60px,7.5vw,92px); font-weight:850; letter-spacing:-.03em; line-height:1.02;
  background:linear-gradient(92deg,var(--lx1) 0%,var(--lx2) 30%,var(--lx3) 65%,var(--lx4) 95%);
  -webkit-background-clip:text; background-clip:text; color:transparent; -webkit-text-fill-color:transparent;
  filter:drop-shadow(0 10px 30px rgba(91,44,255,.25));
}
.eyebrow{ display:inline-block; font-size:12px; letter-spacing:.14em; font-weight:800; color:#fff; background:var(--lx-dark); padding:9px 16px; border-radius:999px; }
.eyebrow::before{ content:"●"; color:#00ffb2; margin-right:8px; font-size:10px; animation:lx-blink 1.6s infinite; }
@keyframes lx-blink{ 50%{ opacity:.35; } }
.lede{ font-size:clamp(21px,2.8vw,26px); font-weight:550; }
.hero-support{ color:var(--ink-muted,#6b655e); font-style:italic; }
.hero-actions{ display:flex; gap:12px; flex-wrap:wrap; }
.hero-actions .btn{ border-radius:999px; padding:16px 32px; font-size:16px; font-weight:750; border:0; background:linear-gradient(135deg,#5b2cff,#7a5cff 55%,#00c2a8 140%); color:#fff; box-shadow:0 10px 28px rgba(109,92,255,.32); text-decoration:none; transition:transform .2s, box-shadow .2s; }
.hero-actions .btn:hover{ transform:translateY(-2px); box-shadow:0 16px 36px rgba(109,92,255,.4); }
.hero-actions .btn.secondary{ background:var(--lx-dark); color:#fff; }
.proof.lx-proof{ display:flex; flex-wrap:wrap; gap:8px; }
.lx-stat{ background:var(--lx-dark); color:#e8e6ff; border-radius:999px; padding:10px 18px; font-size:14.5px; }
.lx-stat b{ background:linear-gradient(90deg,#b7a6ff,#5cf2d6); -webkit-background-clip:text; background-clip:text; color:transparent; -webkit-text-fill-color:transparent; }
ul.personas{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:14px; list-style:none; padding:0; }
ul.personas li{ background:var(--paper-raised,#fff); border:1px solid var(--line,#e4ddd0); border-radius:18px; position:relative; overflow:hidden; transition:transform .25s, box-shadow .25s; }
ul.personas li::before{ content:""; position:absolute; inset:0 0 auto 0; height:3px; background:linear-gradient(90deg,var(--lx1),var(--lx3),var(--lx4)); }
ul.personas li:hover{ transform:translateY(-4px); box-shadow:0 16px 40px rgba(0,0,0,.12); }
.zone{ border:1px solid var(--line,#e4ddd0); border-radius:22px; padding:22px; box-shadow:0 6px 28px rgba(0,0,0,.05); }
.zone > h2{ font-size:13px; letter-spacing:.12em; text-transform:uppercase; color:#6d5cff; display:flex; gap:10px; align-items:center; }
.zone > h2::after{ content:""; height:1px; flex:1; background:linear-gradient(90deg,rgba(109,92,255,.4),transparent); }
.card-grid .card{ background:#fff; border-radius:18px; transition:transform .25s, box-shadow .25s; }
.card-grid .card:hover{ transform:translateY(-5px); box-shadow:0 18px 44px rgba(0,0,0,.12); }
footer{ background:var(--lx-dark); color:#fff; border-radius:20px; padding:18px; text-align:center; }
.lx-reveal{ opacity:0; transform:translateY(18px); transition:opacity .6s, transform .6s; }
.lx-reveal.lx-in{ opacity:1; transform:none; }
::selection{ background:#5b2cff; color:#fff; }
@media (prefers-reduced-motion:reduce){ .lx-orbs::before,.lx-orbs::after,.eyebrow::before{ animation:none; } .lx-reveal{ opacity:1; transform:none; } }
`;

const JS = `// lx-polish client enhancements — orbs, stat pills, icons, reveal
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
`;

function walk(dir, out=[]) {
  for (const e of fs.readdirSync(dir, {withFileTypes:true})) {
    if (e.name.startsWith('.') || e.name==='node_modules' || e.name==='dist') continue;
    const p=path.join(dir,e.name);
    if (e.isDirectory()) walk(p,out); else out.push(p);
  }
  return out;
}

const files = walk(ROOT);
const find = (re) => files.find(f=>re.test(f.replace(/\\/g,'/')));
const layout = find(/src\/layouts\/.*\.astro$/) || find(/src\/.*[Ll]ayout.*\.astro$/);
const index = find(/src\/pages\/index\.astro$/);
if (!layout) { console.error('No layout found under src/layouts'); process.exit(1); }
if (!index) { console.error('No src/pages/index.astro found'); process.exit(1); }

console.log('layout:', path.relative(ROOT,layout));
console.log('index :', path.relative(ROOT,index));

const cssPath = path.join(ROOT,'src/styles/lx-polish.css');
const jsPath = path.join(ROOT,'src/scripts/lx-polish.js');

function writeFile(p, content, label) {
  const rel = path.relative(ROOT,p);
  if (fs.existsSync(p) && fs.readFileSync(p,'utf8')===content) { console.log('unchanged '+rel); return; }
  if (!WRITE) { console.log('[dry-run] would write '+rel); return; }
  if (fs.existsSync(p)) fs.copyFileSync(p, p+'.bak');
  fs.mkdirSync(path.dirname(p),{recursive:true});
  fs.writeFileSync(p,content);
  console.log((fs.existsSync(p+'.bak')?'patched ':'wrote ')+rel);
}

writeFile(cssPath, CSS, 'css');
writeFile(jsPath, JS, 'js');

// patch layout to import both
let txt = fs.readFileSync(layout,'utf8');
let next = txt;
if (!/lx-polish\.css/.test(next)) {
  next = next.replace(/(---\s*\n[\s\S]*?)(\n---)/, `$1\nimport "../styles/lx-polish.css";$2`);
  if (next===txt) next = `---\nimport "../styles/lx-polish.css";\n---\n`+next;
}
if (!/lx-polish\.js/.test(next)) {
  if (next.includes('</head>')) next = next.replace('</head>', `  <script src="../scripts/lx-polish.js" defer></script>\n</head>`);
  else next += `\n<script src="../scripts/lx-polish.js" defer></script>\n`;
}
if (next!==txt) {
  if (!WRITE) console.log('[dry-run] would patch layout imports');
  else { fs.copyFileSync(layout, layout+'.bak'); fs.writeFileSync(layout,next); console.log('patched layout imports'); }
} else console.log('layout imports already present');
console.log(WRITE ? 'done. rebuild to verify.' : 'dry-run done. re-run with --write to apply.');
