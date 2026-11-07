/* Pen-drawn flying birds for "Where the storks go": a white stork, an osprey, a common cuckoo and a marsh harrier,
 * seen from above with the head pointing up (north), drawn in iron-gall ink with a thin watercolour wash in the palette of
 * The Inked World (js/ink-palette.js). Two wing frames each (spread and downstroke), plus a nest, a cross and a funnel mark.
 * PenBirds.canvas(kind, frame, px) returns a canvas px wide; PenBirds.addTo(map) registers every sprite with MapLibre.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function (global) {
  'use strict';
  const P = global.InkPalette || { ink: '#2B2119', paper: '#F3E5BF', red: '#A3261B', pigments: {} };
  const PG = P.pigments || {};
  const INK = P.ink, SCALE = 3;
  function rng(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }

  // a hand-drawn closed or open path through points (quadratic smoothing, a little wobble)
  function path(ctx, pts, closed, wob, R) {
    const q = pts.map(p => [p[0] + (R() - 0.5) * wob, p[1] + (R() - 0.5) * wob]);
    ctx.beginPath();
    if (q.length < 3) { ctx.moveTo(q[0][0], q[0][1]); q.slice(1).forEach(p => ctx.lineTo(p[0], p[1])); return; }
    const n = q.length, m = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    if (closed) {
      let s = m(q[n - 1], q[0]); ctx.moveTo(s[0], s[1]);
      for (let i = 0; i < n; i++) { const e = m(q[i], q[(i + 1) % n]); ctx.quadraticCurveTo(q[i][0], q[i][1], e[0], e[1]); }
      ctx.closePath();
    } else {
      ctx.moveTo(q[0][0], q[0][1]);
      for (let i = 1; i < n - 1; i++) { const e = m(q[i], q[i + 1]); ctx.quadraticCurveTo(q[i][0], q[i][1], e[0], e[1]); }
      ctx.lineTo(q[n - 1][0], q[n - 1][1]);
    }
  }
  const mirror = pts => pts.map(p => [-p[0], p[1]]).reverse();

  // species drawings in a 64 x 64 box centred on 0,0, head up; f = 0 spread, 1 downstroke (wings shorter, tips forward)
  const SPEC = {
    stork(c, f, R) {
      // a white stork seen from above in flight: long straight wings, black flight feathers and fingered tips,
      // neck stretched forward to a long red bill, red legs trailing well beyond the short white tail
      const k = f ? 0.84 : 1, dy = f ? 1.6 : 0;
      const W = (x, y) => [x * k, y + dy * (x / 30)];
      const wing = [W(2.6, -4.2), W(10, -5.2), W(19, -5.4), W(26, -4.8), W(29.5, -3.6), W(31, -1.5), W(30.6, 1), W(28.4, 3), W(20, 3.6), W(10, 4.2), W(2.6, 4.6)];
      const black = [W(2.6, 4.6), W(10, 4.2), W(20, 3.6), W(28.4, 3), W(30.6, 1), W(31, -1.5), W(29.5, -3.6), W(26, -4.8), W(23, -1.4), W(16, 0.2), W(8, 0.6), W(2.6, 0.8)];
      [wing, mirror(wing)].forEach((w, side) => {
        path(c, w, true, 0.35, R); c.fillStyle = '#FBF7EC'; c.fill();
        path(c, side ? mirror(black) : black, true, 0.3, R); c.fillStyle = 'rgba(30,24,19,0.95)'; c.fill();
        path(c, w, true, 0.35, R); c.lineWidth = 1.1; c.strokeStyle = INK; c.stroke();
        // separated primary fingers at the tip
        const s = side ? -1 : 1; c.lineWidth = 1.4; c.strokeStyle = 'rgba(30,24,19,0.95)';
        for (let i = 0; i < 4; i++) { const y0 = -3.4 + i * 1.7 + dy; c.beginPath(); c.moveTo(s * 28 * k, y0); c.lineTo(s * 32.2 * k, y0 + 0.5 + i * 0.35); c.stroke(); }
        // a few covert lines on the white
        c.lineWidth = 0.5; c.strokeStyle = 'rgba(43,33,25,0.45)';
        for (let i = 0; i < 4; i++) { const x = 6 + i * 5; c.beginPath(); c.moveTo(s * x * k, -4.2 + dy * (x / 30)); c.lineTo(s * (x + 2) * k, -0.2 + dy * (x / 30)); c.stroke(); }
      });
      // red legs trailing far behind
      c.strokeStyle = P.red; c.lineWidth = 1.5; c.lineCap = 'round';
      [[-1.2, 11, -1.9, 31], [1.2, 11, 1.9, 31]].forEach(l => { c.beginPath(); c.moveTo(l[0], l[1]); c.lineTo(l[2], l[3]); c.stroke(); });
      // short white tail
      path(c, [[-3, 8], [-2.6, 14.5], [0, 15.6], [2.6, 14.5], [3, 8]], true, 0.3, R); c.fillStyle = '#FBF7EC'; c.fill(); c.lineWidth = 0.9; c.strokeStyle = INK; c.stroke();
      // slim body
      path(c, [[0, -9], [2.6, -5], [3.2, 2], [2.6, 9], [0, 11.5], [-2.6, 9], [-3.2, 2], [-2.6, -5]], true, 0.3, R); c.fillStyle = '#FBF7EC'; c.fill(); c.lineWidth = 1.1; c.strokeStyle = INK; c.stroke();
      // the long neck stretched forward, small head, long red bill
      c.beginPath(); c.moveTo(0, -8); c.lineTo(0, -19.5); c.lineWidth = 3; c.strokeStyle = INK; c.stroke(); c.lineWidth = 1.7; c.strokeStyle = '#FBF7EC'; c.stroke();
      c.beginPath(); c.ellipse(0, -21, 1.9, 2.4, 0, 0, 7); c.fillStyle = '#FBF7EC'; c.fill(); c.lineWidth = 0.9; c.strokeStyle = INK; c.stroke();
      c.beginPath(); c.moveTo(-0.95, -22.8); c.lineTo(0, -32); c.lineTo(0.95, -22.8); c.closePath(); c.fillStyle = P.red; c.fill(); c.lineWidth = 0.6; c.strokeStyle = '#6E1A12'; c.stroke();
    },
    osprey(c, f, R) {
      const k = f ? 0.82 : 1, dy = f ? 2.4 : 0;
      const W = (x, y) => [x * k, y + dy * (x / 30)];
      // the crooked gull wing: carpal joint thrust forward
      const wing = [W(3, -3), W(9, -5.5), W(14, -7.6), W(20, -5.8), W(26, -2.4), W(30.5, 1.2), W(31, 3.4), W(29, 4.6), W(23, 4.4), W(16, 3.2), W(12, 5.4), W(6, 6.2), W(3, 6)];
      [wing, mirror(wing)].forEach(w => {
        path(c, w, true, 0.5, R); c.fillStyle = PG.umberDeep || '#664C36'; c.fill(); c.lineWidth = 1.2; c.strokeStyle = INK; c.stroke();
      });
      // hatching on the wings, the dark carpal and the barred flight feathers
      c.lineWidth = 0.55; c.strokeStyle = 'rgba(251,243,220,0.55)';
      for (let s = -1; s <= 1; s += 2) for (let i = 0; i < 6; i++) { const x = 15 + i * 2.6; c.beginPath(); c.moveTo(s * x * k, -3 + i * 0.6 + dy * (x / 30)); c.lineTo(s * (x + 1.6) * k, 3.4 + dy * (x / 30)); c.stroke(); }
      // tail, barred
      path(c, [[-3.3, 8], [-3.6, 18], [0, 19], [3.6, 18], [3.3, 8]], true, 0.3, R); c.fillStyle = PG.umber || '#8A6A4E'; c.fill(); c.lineWidth = 1; c.strokeStyle = INK; c.stroke();
      c.lineWidth = 0.7; for (let i = 0; i < 3; i++) { c.beginPath(); c.moveTo(-3.4, 11 + i * 2.6); c.lineTo(3.4, 11 + i * 2.6); c.stroke(); }
      // body and the white head with its dark eye stripe
      path(c, [[0, -8], [3.4, -4], [4, 3], [3, 9], [0, 10.5], [-3, 9], [-4, 3], [-3.4, -4]], true, 0.4, R); c.fillStyle = PG.umberDeep || '#664C36'; c.fill(); c.lineWidth = 1.1; c.strokeStyle = INK; c.stroke();
      c.beginPath(); c.arc(0, -10.5, 3.3, 0, 7); c.fillStyle = '#FBF7EC'; c.fill(); c.lineWidth = 1; c.stroke();
      c.beginPath(); c.moveTo(-3, -10); c.lineTo(-1, -11); c.moveTo(3, -10); c.lineTo(1, -11); c.lineWidth = 1; c.stroke();
      c.beginPath(); c.moveTo(-1, -13.4); c.quadraticCurveTo(0, -16.5, 1, -13.4); c.fillStyle = INK; c.fill();
    },
    cuckoo(c, f, R) {
      const k = f ? 0.8 : 1, dy = f ? 2 : 0;
      const W = (x, y) => [x * k, y + dy * (x / 22)];
      // pointed, swept wings like a small falcon
      const wing = [W(2.5, -3), W(10, -2.8), W(17, 0.6), W(23.5, 6.2), W(17, 6.2), W(9, 5.4), W(2.5, 4.6)];
      [wing, mirror(wing)].forEach(w => { path(c, w, true, 0.4, R); c.fillStyle = '#8D9196'; c.fill(); c.lineWidth = 1.1; c.strokeStyle = INK; c.stroke(); });
      c.lineWidth = 0.5; c.strokeStyle = 'rgba(43,33,25,0.6)';
      for (let s = -1; s <= 1; s += 2) for (let i = 0; i < 4; i++) { const x = 8 + i * 3.4; c.beginPath(); c.moveTo(s * x * k, 0.6 + i * 0.8 + dy * (x / 22)); c.lineTo(s * (x + 2.4) * k, 5.2 + dy * (x / 22)); c.stroke(); }
      // the long graduated tail with white tips
      path(c, [[-2.4, 6], [-3.2, 17], [-1.6, 22.5], [0, 23.4], [1.6, 22.5], [3.2, 17], [2.4, 6]], true, 0.3, R); c.fillStyle = '#5E6266'; c.fill(); c.lineWidth = 1; c.strokeStyle = INK; c.stroke();
      c.fillStyle = '#FBF7EC'; [[-2.2, 12], [2.2, 12], [-2.6, 16.5], [2.6, 16.5], [0, 21.5]].forEach(p => { c.beginPath(); c.arc(p[0], p[1], 0.75, 0, 7); c.fill(); });
      path(c, [[0, -6.5], [2.6, -3], [2.9, 3], [2.2, 7], [0, 8], [-2.2, 7], [-2.9, 3], [-2.6, -3]], true, 0.3, R); c.fillStyle = '#8D9196'; c.fill(); c.lineWidth = 1; c.stroke();
      c.beginPath(); c.arc(0, -7.6, 2.4, 0, 7); c.fillStyle = '#8D9196'; c.fill(); c.stroke();
      c.beginPath(); c.moveTo(-0.7, -9.6); c.lineTo(0, -12); c.lineTo(0.7, -9.6); c.fillStyle = INK; c.fill();
      c.beginPath(); c.arc(-1.1, -8.2, 0.55, 0, 7); c.arc(1.1, -8.2, 0.55, 0, 7); c.fillStyle = '#E3A14A'; c.fill();
    },
    harrier(c, f, R) {
      const k = f ? 0.82 : 1, dy = f ? 2.2 : 0;
      const W = (x, y) => [x * k, y + dy * (x / 30)];
      const wing = [W(3, -3), W(12, -5), W(21, -4.6), W(27.5, -2.6), W(30.5, 0.6), W(30, 3.6), W(27, 6), W(18, 6.8), W(9, 6.6), W(3, 6)];
      [wing, mirror(wing)].forEach(w => { path(c, w, true, 0.5, R); c.fillStyle = '#6B4A2E'; c.fill(); c.lineWidth = 1.2; c.strokeStyle = INK; c.stroke(); });
      // the female's cream leading edge (shoulder patches) and dark fingers
      c.lineWidth = 1.6; c.strokeStyle = '#E9D7AE';
      for (let s = -1; s <= 1; s += 2) { c.beginPath(); c.moveTo(s * 4 * k, -2.4); c.lineTo(s * 11 * k, -4 + dy * 0.36); c.stroke(); }
      c.lineWidth = 0.8; c.strokeStyle = 'rgba(30,22,16,0.9)';
      for (let s = -1; s <= 1; s += 2) for (let i = 0; i < 4; i++) { c.beginPath(); c.moveTo(s * 26.5 * k, -1.6 + i * 2 + dy); c.lineTo(s * 30 * k, -0.9 + i * 1.7 + dy); c.stroke(); }
      path(c, [[-2.8, 8], [-3.2, 20], [0, 21], [3.2, 20], [2.8, 8]], true, 0.3, R); c.fillStyle = '#7A5636'; c.fill(); c.lineWidth = 1; c.strokeStyle = INK; c.stroke();
      path(c, [[0, -7.5], [3.2, -4], [3.8, 3], [2.9, 9], [0, 10.4], [-2.9, 9], [-3.8, 3], [-3.2, -4]], true, 0.4, R); c.fillStyle = '#6B4A2E'; c.fill(); c.lineWidth = 1.1; c.stroke();
      c.beginPath(); c.arc(0, -9.6, 3, 0, 7); c.fillStyle = '#E9D7AE'; c.fill(); c.lineWidth = 1; c.stroke();
      c.beginPath(); c.moveTo(-0.9, -12.3); c.quadraticCurveTo(0, -14.8, 0.9, -12.3); c.fillStyle = INK; c.fill();
    },
    nest(c, f, R) {   // a stick nest seen from the side
      c.strokeStyle = INK; c.lineWidth = 1.1;
      path(c, [[-13, -2], [-9, 7], [0, 10], [9, 7], [13, -2]], false, 0.6, R); c.stroke();
      for (let i = 0; i < 9; i++) { const y = -1 + R() * 9; c.beginPath(); c.moveTo(-13 + R() * 6, y); c.lineTo(5 + R() * 9, y + (R() - 0.5) * 4); c.lineWidth = 0.7; c.stroke(); }
      c.beginPath(); c.moveTo(-14, -2.5); c.lineTo(14, -2.5); c.lineWidth = 1.2; c.stroke();
    },
    cross(c, f, R) {  // where a tag fell silent and the bird was found dead
      c.strokeStyle = INK; c.lineWidth = 2.2; c.lineCap = 'round';
      c.beginPath(); c.moveTo(0, -11); c.lineTo(0, 12); c.moveTo(-6.5, -4); c.lineTo(6.5, -4); c.stroke();
      c.strokeStyle = P.paper; c.lineWidth = 0.7; c.beginPath(); c.moveTo(0, -9); c.lineTo(0, 10); c.stroke();
    },
    gate(c, f, R) {   // a pair of pen chevrons, the funnel where the birds squeeze through
      c.strokeStyle = P.red; c.lineWidth = 2; c.lineJoin = 'round';
      [[-1], [1]].forEach(([s]) => { path(c, [[s * 13, -11], [s * 4, 0], [s * 13, 11]], false, 0.4, R); c.stroke(); });
      c.beginPath(); c.arc(0, 0, 2.2, 0, 7); c.fillStyle = P.red; c.fill();
    },
  };
  const SIZE = { stork: 44, osprey: 34, cuckoo: 26, harrier: 34, nest: 20, cross: 14, gate: 22 };

  // draw one sprite: px = width in CSS pixels; the canvas is SCALE times larger
  function canvas(kind, frame, px, scale) {
    const sc = scale || SCALE, w = Math.round((px || SIZE[kind]) * sc), cv = document.createElement('canvas');
    cv.width = w; cv.height = w;
    const c = cv.getContext('2d'), fit = kind === 'stork' ? 70 : 64; c.translate(w / 2, w / 2); c.scale(w / fit, w / fit);
    c.lineJoin = 'round'; c.lineCap = 'round';
    // a soft paper halo so the bird reads over any line
    c.save(); c.shadowColor = 'rgba(243,229,191,0.95)'; c.shadowBlur = 6 * sc;
    SPEC[kind](c, frame || 0, rng(kind.length * 977 + (frame || 0) * 31));
    c.restore();
    return cv;
  }
  function addTo(map) {
    Object.keys(SPEC).forEach(k => {
      [0, 1].forEach(fr => {
        if (fr && !['stork', 'osprey', 'cuckoo', 'harrier'].includes(k)) return;
        const cv = canvas(k, fr), id = `pb-${k}-${fr}`;
        const d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height);
        if (!map.hasImage(id)) map.addImage(id, { width: cv.width, height: cv.height, data: new Uint8Array(d.data.buffer) }, { pixelRatio: SCALE });
      });
    });
  }
  // an inline <img> of a sprite for legends and stories
  function img(kind, px) { const i = new Image(); i.src = canvas(kind, 0, px || SIZE[kind], 2).toDataURL(); i.width = px || SIZE[kind]; i.height = px || SIZE[kind]; i.alt = ''; return i; }
  global.PenBirds = { canvas, addTo, img, SIZE, SCALE };
})(window);
