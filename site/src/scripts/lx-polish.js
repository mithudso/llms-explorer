// lx-polish client enhancement: the proof line's "a · b · c" figures become
// one pill per figure. Nothing else runs on the client; the page reads the
// same with this script blocked.
(() => {
  if (window.__lxPolish) return; window.__lxPolish = true;
  const proof = document.querySelector('main > p.proof');
  if (proof && !proof.querySelector('a') && !proof.classList.contains('lx-proof')) {
    const parts = proof.textContent.split('·').map(s => s.trim()).filter(Boolean);
    proof.classList.add('lx-proof'); proof.innerHTML = '';
    parts.forEach(t => {
      const s = document.createElement('span'); s.className = 'lx-stat';
      s.innerHTML = t.replace(/([0-9][0-9,]*)/g, '<b>$1</b>'); proof.appendChild(s);
    });
  }
})();
