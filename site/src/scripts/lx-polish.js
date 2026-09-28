// lx-polish client enhancement: the proof line's "a · b · c" figures become
// one pill per figure. Nothing else runs on the client; the page reads the
// same with this script blocked. Built with text nodes, never innerHTML, so
// the page's own text is never reinterpreted as markup.
(() => {
  if (window.__lxPolish) return; window.__lxPolish = true;
  const proof = document.querySelector('main > p.proof');
  if (!proof || proof.querySelector('a') || proof.classList.contains('lx-proof')) return;
  const parts = proof.textContent.split('·').map(s => s.trim()).filter(Boolean);
  proof.classList.add('lx-proof');
  proof.textContent = '';
  for (const part of parts) {
    const pill = document.createElement('span');
    pill.className = 'lx-stat';
    // Alternate plain text and figures: the figures go in <b>, the rest stays text.
    for (const piece of part.split(/([0-9][0-9,]*)/)) {
      if (!piece) continue;
      if (/^[0-9][0-9,]*$/.test(piece)) {
        const b = document.createElement('b');
        b.textContent = piece;
        pill.appendChild(b);
      } else {
        pill.appendChild(document.createTextNode(piece));
      }
    }
    proof.appendChild(pill);
  }
})();
