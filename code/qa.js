// QA: open the page at 1280 and 390 px, check the console, play the animation, select a bird, screenshot to qa/.
// Run from the study folder: node code/qa.js  (serves the folder on a local port; outside tiles may fail offline)
const { chromium } = require('playwright'); const http = require('http'); const fs = require('fs'); const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.geojson': 'application/json', '.png': 'image/png', '.pbf': 'application/x-protobuf', '.ttf': 'font/ttf' };
const srv = http.createServer((q, r) => { const p = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); const f = fs.existsSync(p) && fs.statSync(p).isDirectory() ? path.join(p, 'index.html') : p;
  if (!fs.existsSync(f)) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r); }).listen(0);
(async () => {
  const b = await chromium.launch();
  for (const [w, h, tag] of [[1280, 900, 'desktop'], [390, 844, 'phone']]) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    const errs = [];
    p.on('console', m => { if ((m.type() === 'error' || m.type() === 'warning') && !/tile|cartocdn|arcgisonline|fonts.g|Failed to load resource|ERR_|net::|WebGL|GL Driver|GroupMarker/i.test(m.text())) errs.push(m.text()); });
    p.on('pageerror', e => errs.push('PAGEERROR ' + e.message));
    const ML = process.env.MAPLIBRE_DIR || '/home/claude/work/new6/bird-migration/node_modules/maplibre-gl/dist';
    await p.route(/cdn\.jsdelivr\.net\/npm\/maplibre-gl@4\.7\.1\/dist\/(.*)$/, (r) => { const f = path.join(ML, r.request().url().split('/dist/')[1]);
      if (fs.existsSync(f)) r.fulfill({ path: f, contentType: f.endsWith('.css') ? 'text/css' : 'text/javascript' }); else r.abort(); });
    await p.route(/^https:\/\/(?!cdn\.jsdelivr)/, r => r.abort());
    await p.goto('http://localhost:' + srv.address().port + '/', { waitUntil: 'load' });
    await p.waitForTimeout(4000);
    await p.locator('#atlas').scrollIntoViewIfNeeded();
    await p.click('#play'); await p.waitForTimeout(6000);
    await p.screenshot({ path: `${ROOT}/qa/${tag}_map.png` });
    await p.screenshot({ path: `${ROOT}/qa/${tag}_full.jpg`, fullPage: true, type: 'jpeg', quality: 60 });
    await p.click('.lyrBtn'); await p.waitForTimeout(500); await p.click('.lyrPanel input[data-l="modern"]'); await p.waitForTimeout(800);
    await p.locator('#atlas').scrollIntoViewIfNeeded(); await p.screenshot({ path: `${ROOT}/qa/${tag}_layers.png` });
    await p.click('.lyrPanel .reset'); await p.click('.lyrBtn');
    await p.fill('#q', 'Lilla'); await p.waitForTimeout(300); await p.keyboard.press('Enter'); await p.waitForTimeout(5000);
    await p.locator('#atlas').scrollIntoViewIfNeeded();
    await p.screenshot({ path: `${ROOT}/qa/${tag}_follow.png` });
    const sw = await p.evaluate(() => document.documentElement.scrollWidth);
    console.log(tag, 'scrollWidth', sw, 'errors', JSON.stringify(errs));
    await p.close();
  }
  await b.close(); srv.close();
})();
