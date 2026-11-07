// Render the pen-drawn sprites (js/pen-birds.js) to PNG for the static figures, header and collage: node code/sprites.js
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
const ROOT = path.resolve(__dirname, '..');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  await p.setContent('<html><body></body></html>');
  await p.addScriptTag({ path: path.join(ROOT, 'js/ink-palette.js') }); await p.addScriptTag({ path: path.join(ROOT, 'js/pen-birds.js') });
  const out = await p.evaluate(() => { const o = {}; ['stork', 'osprey', 'cuckoo', 'harrier', 'nest', 'cross', 'gate'].forEach(k => { o[k] = PenBirds.canvas(k, 0, 64, 4).toDataURL(); }); return o; });
  fs.mkdirSync(path.join(ROOT, 'img/sprites'), { recursive: true });
  for (const [k, v] of Object.entries(out)) fs.writeFileSync(path.join(ROOT, `img/sprites/${k}.png`), Buffer.from(v.split(',')[1], 'base64'));
  await b.close(); console.log(Object.keys(out).join(' '));
})();
