// Drawing on a chart: Sharif's own marks (placed, moved, resized, removed) over read-only marks from someone else.
//   const layer = marksLayer(chart, series, el, {list, under, changed, times, tfName, color})
//     list()      his marks for this chart's instrument, edited in place; a mark is
//                 {shape: "level" | "zone" | "line" | "vline", kind, side, tf, price | top,bottom | p0,p1, t0, t1, uid}
//     under()     read-only marks drawn beneath his (Claude's): the same shapes plus {color, label, nofill}
//     changed()   called after any add / move / delete
//     times()     the candle times (seconds) of this chart, ascending
//     tfName()    this chart's timeframe, stamped on a new mark
//     color(v)    resolves a CSS variable (--bs --ss --area --mine --panel)
// Pick a type, then click (a level or a vertical line runs from there) or drag (a zone or a line needs a drag).
// The type switches off after one placement. Click a mark to select it; drag its body or its ends; Delete / Backspace
// or right-click removes it; Esc deselects; G = grab (the chart holds still and marks are easy to pick up).
const MOVES = ["displacement", "fake push"];   // a move: an arrow at its end; a fake push is dashed
const arrowHead = (g, x0, y0, x1, y1) => { const a = Math.atan2(y1 - y0, x1 - x0), L = 10; g.setLineDash([]); g.beginPath();
  for (const s of [-0.45, 0.45]) { g.moveTo(x1, y1); g.lineTo(x1 - L * Math.cos(a + s), y1 - L * Math.sin(a + s)); } g.stroke(); };
// [side, shape, kinds]: his vocabulary for marking a chart. The opening range gap is left out (he dropped it).
const MARK_PALETTE = [
  ["buyside", "level", ["buyside", "EQH"]],
  ["sellside", "level", ["sellside", "EQL"]],
  ["", "level", ["BOS", "level behind", "level ahead"]],
  ["", "vline", ["→ bull", "→ bear"]],
  ["", "line", ["trendline", "displacement", "fake push"]],
  ["area", "zone", ["BISI", "SIBI", "IFVG", "VI", "BPR", "order block", "breaker", "mitigation block", "rejection block"]],
  ["area", "zone", ["gap", "liquidity void", "NWOG", "NDOG"]],
];

function marksLayer(chart, series, el, o) {
  const STUB = 36;                                    // an open mark stops this far past the last candle, not at the right edge
  let grab = false, place = null, sel = null, held = null, dirty = 1, sig = "";
  const G = () => grab ? 16 : 6;
  const ts = chart.timeScale();
  const T = () => o.times() || [];
  function idxOf(t) {
    const a = T(), n = a.length; if (!n) return 0;
    const s1 = n > 1 ? a[n - 1] - a[n - 2] : 1, s0 = n > 1 ? a[1] - a[0] : 1;
    if (t <= a[0]) return (t - a[0]) / s0;
    if (t >= a[n - 1]) return n - 1 + (t - a[n - 1]) / s1;
    let lo = 0, hi = n - 1;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (a[m] <= t) lo = m; else hi = m; }
    return lo + (t - a[lo]) / (a[hi] - a[lo]);
  }
  function tOfIdx(l) {
    const a = T(), n = a.length; if (!n) return 0;
    const s1 = n > 1 ? a[n - 1] - a[n - 2] : 1, s0 = n > 1 ? a[1] - a[0] : 1;
    if (l <= 0) return a[0] + l * s0;
    if (l >= n - 1) return a[n - 1] + (l - n + 1) * s1;
    const i = Math.floor(l); return a[i] + (l - i) * (a[i + 1] - a[i]);
  }
  // the chart maps only whole candles inside the data, so go via the nearest real candle plus the candle spacing
  const clampI = l => Math.max(0, Math.min(T().length - 1, Math.round(l)));
  const xOf = t => { if (!T().length) return null; const l = idxOf(t), k = clampI(l), c = ts.logicalToCoordinate(k);
    return c == null ? null : c + (l - k) * ts.options().barSpacing; };
  const tOfX = x => { if (!T().length) return null; const g = ts.coordinateToLogical(x), k = clampI(g == null ? 0 : g),
    c = ts.logicalToCoordinate(k); return c == null ? null : Math.round(tOfIdx(k + (x - c) / ts.options().barSpacing)); };
  const yOf = p => series.priceToCoordinate(p);
  const pOfY = y => { const p = series.coordinateToPrice(y); return p == null ? null : +p.toPrecision(7); };
  const xLast = () => { const a = T(); return a.length ? xOf(a[a.length - 1]) : null; };
  const xEnd = m => m.t1 != null ? xOf(m.t1) : (xLast() == null ? null : xLast() + STUB);
  const col = m => o.color(m.side === "buyside" ? "--bs" : m.side === "sellside" ? "--ss" : m.side === "area" ? "--area" : "--mine");
  const name = m => "S · " + m.kind + (m.side === "buyside" ? " ↑" : m.side === "sellside" ? " ↓" : "");

  function setGrab(on) {
    grab = on; place = null;
    chart.applyOptions({ handleScroll: !on, handleScale: !on });
    el.style.cursor = on ? "grab" : "";
    if (o.onMode) o.onMode();
  }
  function setPlace(p) {
    place = p; if (p) grab = false;
    chart.applyOptions({ handleScroll: !p && !grab, handleScale: !p && !grab });
    el.style.cursor = p ? "crosshair" : grab ? "grab" : "";
  }

  // ---- paint
  const cv = document.createElement("canvas");
  cv.style.cssText = "position:absolute;left:0;top:0;pointer-events:none;z-index:3";
  if (getComputedStyle(el).position === "static") el.style.position = "relative";
  el.appendChild(cv);
  function tag(g, text, x, y, color, bold) {
    g.font = (bold ? "bold 12px" : "11px") + " ui-monospace, Menlo, monospace";
    const w = g.measureText(text).width;
    g.fillStyle = "rgba(0,0,0,.72)"; g.fillRect(x - 3, y - 8, w + 6, 16); g.fillStyle = color; g.fillText(text, x, y);
  }
  function paint() {
    const W = ts.width(), H = el.clientHeight - ts.height(), r = devicePixelRatio || 1;
    if (cv.width !== Math.round(el.clientWidth * r) || cv.height !== Math.round(el.clientHeight * r)) {
      cv.width = Math.round(el.clientWidth * r); cv.height = Math.round(el.clientHeight * r);
      cv.style.width = el.clientWidth + "px"; cv.style.height = el.clientHeight + "px";
    }
    const g = cv.getContext("2d");
    g.setTransform(r, 0, 0, r, 0, 0); g.clearRect(0, 0, el.clientWidth, el.clientHeight);
    g.save(); g.beginPath(); g.rect(0, 0, W, H); g.clip(); g.textBaseline = "middle";
    for (const u of (o.under ? o.under() : [])) {       // someone else's marks: read-only, never picked up, drawn as strongly as his own
      const x0 = u.t0 == null ? 0 : xOf(u.t0), xl = xLast();
      const x1 = u.t1 == null ? (xl == null ? W : Math.min(W, xl + STUB)) : xOf(u.t1); if (x0 == null || x1 == null) continue;
      g.strokeStyle = g.fillStyle = u.color; g.lineWidth = 2; g.setLineDash([]);
      let tx = Math.max(x0, 0) + 4, ty;
      if (u.shape === "vline") {
        g.setLineDash([6, 4]); g.beginPath(); g.moveTo(x0, 0); g.lineTo(x0, H); g.stroke(); g.setLineDash([]); tx = x0 + 6; ty = 14;
      } else if (u.shape === "line") {
        const y0 = yOf(u.p0), y1 = yOf(u.p1); if (y0 == null || y1 == null) continue;
        g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke(); if (MOVES.includes(u.kind)) arrowHead(g, x0, y0, x1, y1);
        tx = (x0 + x1) / 2 + 6; ty = (y0 + y1) / 2;
      } else if (u.shape === "zone") {
        const a = yOf(u.top), b = yOf(u.bottom); if (a == null || b == null) continue;
        if (!u.nofill) { g.globalAlpha = .22; g.fillRect(x0, a, x1 - x0, b - a); g.globalAlpha = 1; }   // a far higher timeframe's zone: edges only
        g.strokeRect(x0, a, x1 - x0, b - a); ty = Math.min(a, b) - 9;
      } else {
        const y = yOf(u.price); if (y == null) continue;
        g.beginPath(); g.moveTo(x0, y); g.lineTo(x1, y); g.stroke(); ty = y - 9;
      }
      tag(g, u.label, tx, ty, u.color, true);
    }
    o.list().forEach((m, i) => {
      const x0 = m.t0 == null ? 0 : xOf(m.t0), x1 = xEnd(m), on = sel === i;
      if (x0 == null || x1 == null) return;
      g.strokeStyle = g.fillStyle = col(m); g.lineWidth = on ? 3 : 2; g.setLineDash(m.shape === "zone" ? [5, 4] : []);
      g.font = "11px ui-monospace, Menlo, monospace";
      const handles = [];
      if (m.shape === "vline") {
        g.setLineDash([6, 4]); g.beginPath(); g.moveTo(x0, 0); g.lineTo(x0, H); g.stroke(); g.setLineDash([]);
        g.fillText(name(m), x0 + 6, 30); handles.push([x0, 30]);
      } else if (m.shape === "line") {
        const y0 = yOf(m.p0), y1 = yOf(m.p1); if (y0 == null || y1 == null) return;
        if (m.kind === "fake push") g.setLineDash([6, 4]);
        g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
        if (MOVES.includes(m.kind)) arrowHead(g, x0, y0, x1, y1);
        g.fillText(name(m), Math.min(x1, W) + 4, y1); handles.push([x0, y0], [x1, y1]);
      } else if (m.shape === "zone") {
        const a = yOf(m.top), b = yOf(m.bottom); if (a == null || b == null) return;
        g.globalAlpha = on ? .28 : .14; g.fillRect(x0, a, x1 - x0, b - a); g.globalAlpha = 1;
        g.beginPath(); g.moveTo(x0, a); g.lineTo(x1, a); g.moveTo(x0, b); g.lineTo(x1, b); g.stroke(); g.setLineDash([]);
        g.textAlign = "right"; g.fillText(name(m), Math.min(x1, W) - 4, Math.min(a, b) - 7); g.textAlign = "left";
        handles.push([x0, a], [x1, a], [x0, b], [x1, b]);
      } else {
        const y = yOf(m.price); if (y == null) return;
        g.beginPath(); g.moveTo(x0, y); g.lineTo(x1, y); g.stroke();
        g.beginPath(); g.arc(x0, y, on ? 4 : 2.5, 0, 7); g.fill();
        g.textAlign = "right"; g.fillText(name(m), Math.min(x1, W) - 4, y + (m.side === "sellside" ? 8 : -8)); g.textAlign = "left";
        handles.push([x0, y], [x1, y]);
      }
      if (on) { g.setLineDash([]); g.fillStyle = o.color("--panel");
        for (const [x, y] of handles) { g.fillRect(x - 4, y - 4, 8, 8); g.strokeRect(x - 4, y - 4, 8, 8); } }
    });
    g.restore();
  }
  let alive = true;
  (function loop() { if (!alive) return; try { tick(); } catch (e) { /* chart not ready yet */ } requestAnimationFrame(loop); })();
  function tick() {
    const lr = ts.getVisibleLogicalRange();
    const s = [dirty, lr && lr.from, lr && lr.to, yOf(100), yOf(101), el.clientWidth, el.clientHeight, o.list().length].join("|");
    if (s !== sig) { sig = s; paint(); }
  }
  const redraw = () => { dirty++; };

  // ---- hit test + interaction
  function hit(px, py) {
    let best = null;
    const take = (i, part, d) => { if (!best || d < best.d) best = { i, part, d }; };
    o.list().forEach((m, i) => {
      const x0 = m.t0 == null ? 0 : xOf(m.t0), x1 = xEnd(m);
      if (x0 == null || x1 == null) return;
      if (m.shape === "vline") { if (Math.abs(px - x0) <= G()) take(i, "body", Math.abs(px - x0)); return; }
      if (px < Math.min(x0, x1) - G() || px > Math.max(x0, x1) + G()) return;
      const end = Math.abs(px - x0) <= G() ? "start" : Math.abs(px - x1) <= G() ? "end" : null;
      if (m.shape === "line") {
        const y0 = yOf(m.p0), y1 = yOf(m.p1); if (y0 == null || y1 == null) return;
        if (Math.hypot(px - x0, py - y0) <= G() + 2) return take(i, "start", 0);
        if (Math.hypot(px - x1, py - y1) <= G() + 2) return take(i, "end", 0);
        const L = Math.hypot(x1 - x0, y1 - y0) || 1, d = Math.abs((y1 - y0) * px - (x1 - x0) * py + x1 * y0 - y1 * x0) / L;
        if (d <= G()) take(i, "body", d);
      } else if (m.shape === "zone") {
        const a = yOf(m.top), b = yOf(m.bottom); if (a == null || b == null) return;
        if (end && py >= a - G() && py <= b + G()) take(i, end, 0);
        else if (Math.abs(py - a) <= G()) take(i, "top", Math.abs(py - a));
        else if (Math.abs(py - b) <= G()) take(i, "bottom", Math.abs(py - b));
        else if (py > a && py < b) take(i, "inside", G());
      } else {
        const y = yOf(m.price); if (y == null || Math.abs(py - y) > G()) return;
        take(i, end || "body", Math.abs(py - y));
      }
    });
    return best;
  }
  const pos = e => { const b = el.getBoundingClientRect(); return [e.clientX - b.left, e.clientY - b.top]; };
  const inPane = ([x, y]) => x >= 0 && x <= ts.width() && y >= 0 && y <= el.clientHeight - ts.height();
  const freeze = on => { if (!place && !grab) chart.applyOptions({ handleScroll: !on, handleScale: !on }); };
  const r2 = v => +v.toPrecision(7);
  const down = e => {
    if (e.button !== 0) return;
    const pt = pos(e); if (!inPane(pt)) return;
    const [px, py] = pt, h = hit(px, py), p = pOfY(py), t = tOfX(px), L = o.list();
    if (h) {
      sel = h.i; held = { i: h.i, part: h.part, p0: p, t0: t, x0: px, y0: py, moved: false, orig: { ...L[h.i] } };
    } else if (place && p != null && t != null) {
      const m = place.shape === "zone" ? { top: p, bottom: p } : place.shape === "line" ? { p0: p, p1: p } : place.shape === "vline" ? {} : { price: p };
      Object.assign(m, { shape: place.shape, kind: place.kind, side: place.side, tf: o.tfName ? o.tfName() : "", t0: t, t1: t,
                         uid: Math.random().toString(36).slice(2, 8), by: "S" });
      L.push(m); sel = L.length - 1;
      held = { i: sel, part: m.shape === "zone" ? "corner" : "end", p0: p, t0: t, x0: px, y0: py, moved: false, fresh: true, orig: { ...m } };
    } else {
      if (sel != null) { sel = null; redraw(); }
      return;                                             // nothing of his: the chart's own handlers get it
    }
    freeze(true); e.preventDefault(); e.stopImmediatePropagation(); redraw();
  };
  const move = e => {
    const [px, py] = pos(e);
    if (!held) { if (!place && inPane([px, py]) && hit(px, py)) el.style.cursor = "move"; else if (!place && el.style.cursor === "move") el.style.cursor = grab ? "grab" : ""; return; }
    if (Math.hypot(px - held.x0, py - held.y0) > 3) held.moved = true;
    if (!held.moved) return;
    const p = pOfY(py), t = tOfX(px); if (p == null || t == null) return;
    const m = o.list()[held.i], q = held.orig, dp = r2(p - held.p0), dt = t - held.t0;
    if (m.shape === "vline") m.t0 = t;
    else if (m.shape === "line") {
      if (held.part === "end") { m.t1 = t; m.p1 = p; } else if (held.part === "start") { m.t0 = t; m.p0 = p; }
      else { m.p0 = r2(q.p0 + dp); m.p1 = r2(q.p1 + dp); m.t0 = q.t0 + dt; if (q.t1 != null) m.t1 = q.t1 + dt; }
    } else if (held.part === "end") m.t1 = t;
    else if (held.part === "start") m.t0 = t;
    else if (held.part === "corner") { m.top = Math.max(q.top, p); m.bottom = Math.min(q.bottom, p); m.t1 = t; }
    else if (held.part === "top") m.top = p;
    else if (held.part === "bottom") m.bottom = p;
    else if (held.part === "inside") { m.top = r2(q.top + dp); m.bottom = r2(q.bottom + dp); if (q.t0 != null) m.t0 = q.t0 + dt; if (q.t1 != null) m.t1 = q.t1 + dt; }
    else m.price = p;
    redraw(); e.preventDefault();
  };
  const up = () => {
    if (!held) return;
    const L = o.list(), m = L[held.i];
    if (held.fresh && !held.moved) {
      if (m.shape === "line") { L.splice(held.i, 1); sel = null; }                // a line needs a drag
      else {
        m.t1 = null;                                                              // a click: from here on
        if (m.shape === "zone") { const h = Math.max(Math.abs(m.top) * 0.0005, 0.0001); m.top = r2(m.top + h); m.bottom = r2(m.bottom - h); }
      }
    }
    const k = L[held.i] === m ? m : null;
    if (k && k.shape === "vline") k.t1 = null;
    if (k && k.t0 != null && k.t1 != null && k.t1 < k.t0) { [k.t0, k.t1] = [k.t1, k.t0]; if (k.shape === "line") [k.p0, k.p1] = [k.p1, k.p0]; }
    if (k && k.shape === "zone" && k.top < k.bottom) [k.top, k.bottom] = [k.bottom, k.top];
    held = null; freeze(false);
    redraw(); o.changed();                                                        // the page ends the placement: one placement per pick
  };
  const menu = e => { const [px, py] = pos(e), h = hit(px, py); if (h) { e.preventDefault(); o.list().splice(h.i, 1); sel = null; redraw(); o.changed(); } };
  const key = e => {
    if (["INPUT", "TEXTAREA", "SELECT"].includes(e.target.tagName)) return;
    if ((e.key === "Delete" || e.key === "Backspace") && sel != null) { e.preventDefault(); o.list().splice(sel, 1); sel = null; redraw(); o.changed(); }
    else if (e.key === "Escape") { sel = null; redraw(); }
  };
  el.addEventListener("pointerdown", down, true);
  el.addEventListener("mousedown", e => { if (held) { e.preventDefault(); e.stopImmediatePropagation(); } }, true);
  window.addEventListener("pointermove", move); window.addEventListener("pointerup", up);
  el.addEventListener("contextmenu", menu); document.addEventListener("keydown", key);
  const destroy = () => { alive = false; window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up); document.removeEventListener("keydown", key); };
  return { redraw, setPlace, setGrab, grabbing: () => grab, deselect: () => { sel = null; redraw(); }, destroy };
}
