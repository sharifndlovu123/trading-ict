// Drawing on a chart: Sharif's own marks (placed, moved, resized, removed) over read-only marks from someone else.
//   const layer = marksLayer(chart, series, el, {list, under, changed, times, tfName, color})
//     list()      his marks for this chart's instrument, edited in place; a mark is
//                 {shape: "level" | "zone" | "line" | "vline", kind, side, tf, price | top,bottom | p0,p1, t0, t1, uid}
//     under()     read-only marks drawn beneath his (Claude's): the same shapes plus {color, label, nofill}
//     changed()   called after any add / move / delete
//     times()     the candle times (seconds) of this chart, ascending
//     candles()   this chart's candles (same order as times()), for snapping
//     snap()      true while snap is on: a point being placed or dragged jumps to the nearest candle's open, high, low
//                 or close, whichever is closest to the mouse, so a mark sits exactly on a price the chart printed
//     tfName()    this chart's timeframe, stamped on a new mark
//     color(v)    resolves a CSS variable (--bs --ss --area --mine --panel)
// Pick a type, then click (a level or a vertical line runs from there) or drag (a zone or a line needs a drag).
// The type switches off after one placement. Click a mark to select it; drag its body or its ends; Delete / Backspace
// or right-click removes it; Esc deselects; G = grab (the chart holds still and marks are easy to pick up).
// Double-click a mark to lock it, and again to unlock it. A locked mark can no longer be picked up, moved or removed,
// and a press goes through it to whatever lies underneath. A selected mark also shows a small bar (lock / delete);
// Shift+click picks up a locked mark. A block's corner handles size it both ways at once; its edges one way.
const MOVES = ["displacement", "fake push"];   // a move: an arrow at its end; a fake push is dashed
const arrowHead = (g, x0, y0, x1, y1) => { const a = Math.atan2(y1 - y0, x1 - x0), L = 10; g.setLineDash([]); g.beginPath();
  for (const s of [-0.45, 0.45]) { g.moveTo(x1, y1); g.lineTo(x1 - L * Math.cos(a + s), y1 - L * Math.sin(a + s)); } g.stroke(); };
// [side, shape, kinds]: his vocabulary for marking a chart. The opening range gap is left out (he dropped it).
const MARK_PALETTE = [
  ["buyside", "level", ["buyside", "EQH"]],
  ["sellside", "level", ["sellside", "EQL"]],
  ["", "level", ["BOS", "level behind", "level ahead"]],
  ["", "vline", ["→ bull", "→ bear"]],
  ["", "line", ["line", "displacement", "fake push"]],
  ["area", "zone", ["FVG", "BISI", "SIBI", "IFVG", "VI", "BPR", "order block", "breaker", "mitigation block", "rejection block"]],
  ["area", "zone", ["NWOG", "NDOG"]],
  ["", "zone", ["trading range"]],
  ["", "level", ["50%"]],
];

// One colour per kind of mark, so a chart with several kinds on it can be read at a glance. The same kind has the same
// colour whoever drew it (Claude's are dashed and labelled "C ·"). Chosen to stand out against blue and black candles
// on a light page and on a dark one.
const KIND_COLOR = {
  "buyside": "#2f80ed", "EQH": "#00a3c4", "sellside": "#f2711c", "EQL": "#d99a00",
  "BOS": "#9b51e0", "level behind": "#e03131", "level ahead": "#2f9e44", "→ bull": "#2f9e44", "→ bear": "#e03131",
  "line": "#7b8794", "trendline": "#7b8794", "displacement": "#12a594", "fake push": "#e64980",
  "FVG": "#e8a200", "BISI": "#0ca678", "SIBI": "#c2255c", "IFVG": "#7950f2", "VI": "#c930c9", "BPR": "#1c7ed6",
  "order block": "#4c6ef5", "breaker": "#d6336c", "mitigation block": "#0b7285", "rejection block": "#a8641a",
  "trading range": "#8d99ae", "50%": "#8d99ae", "NWOG": "#e8890c", "NDOG": "#b8860b",
};
// a mark whose label is free text (Claude's often are) takes the colour of the kind it names
const KIND_WORDS = [["EQH", "EQH"], ["EQL", "EQL"], ["IFVG", "IFVG"], ["FVG", "FVG"], ["BISI", "BISI"], ["SIBI", "SIBI"], ["IFVG", "IFVG"], ["NWOG", "NWOG"], ["NDOG", "NDOG"], ["BPR", "BPR"],
  ["order block", "order block"], ["breaker", "breaker"], ["level behind", "level behind"], ["level ahead", "level ahead"], ["BOS", "BOS"], ["bull", "→ bull"], ["bear", "→ bear"],
  ["buyside", "buyside"], ["PDH", "buyside"], ["PWH", "buyside"], ["high", "buyside"], ["sellside", "sellside"], ["PDL", "sellside"], ["PWL", "sellside"], ["low", "sellside"],
  ["VI", "VI"], ["displacement", "displacement"]];
function markColor(kind, fallback) {
  if (KIND_COLOR[kind]) return KIND_COLOR[kind];
  const k = String(kind || ""); for (const [word, as] of KIND_WORDS) if (new RegExp("(^|[^a-z])" + word + "([^a-z]|$)", "i").test(k)) return KIND_COLOR[as];
  return fallback;
}

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
  const col = m => markColor(m.kind, o.color("--mine"));
  // a block or an imbalance carries its timeframe beside its name: on a lower chart you can tell which timeframe made it
  const name = m => "S · " + m.kind + (m.shape === "zone" && m.tf ? " " + m.tf : "") + (m.side === "buyside" ? " ↑" : m.side === "sellside" ? " ↓" : "") + (m.locked ? " 🔒" : "");
  // snap: the nearest candle to the mouse, and of its open / high / low / close the one closest to the mouse
  let hover = null;                                    // where the snapped point is, while placing or dragging (drawn as a ring)
  function snapAt(px, py) {
    const a = T(), cs = o.candles ? o.candles() : null; if (!o.snap || !o.snap() || !cs || !a.length) return null;
    const g = ts.coordinateToLogical(px), k = clampI(g == null ? 0 : g), c = cs[k]; if (!c) return null;
    let best = null;
    for (const v of [c.open, c.high, c.low, c.close]) { const y = yOf(v); if (y != null && (!best || Math.abs(y - py) < best.d)) best = { d: Math.abs(y - py), p: v, y }; }
    const x = ts.logicalToCoordinate(k);
    return best && x != null ? { t: a[k], p: best.p, x, y: best.y } : null;
  }
  const point = (px, py) => { const sn = snapAt(px, py); hover = sn; return sn ? [sn.p, sn.t] : [pOfY(py), tOfX(px)]; };

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
  const bar = document.createElement("div");           // the small bar for the selected mark: lock / unlock, delete
  bar.style.cssText = "position:absolute;top:30px;left:50%;transform:translateX(-50%);z-index:7;display:none;gap:4px;padding:3px;border-radius:7px;background:rgba(20,22,28,.92);border:1px solid rgba(128,128,128,.4)";
  bar.innerHTML = '<button data-a="lock" style="cursor:pointer;border:0;border-radius:5px;padding:3px 9px;background:none;color:#e7e9ee;font:inherit"></button><button data-a="del" title="remove (Delete)" style="cursor:pointer;border:0;border-radius:5px;padding:3px 9px;background:none;color:#e7e9ee;font:inherit">🗑 Delete</button>';
  el.appendChild(bar);
  for (const ev of ["pointerdown", "mousedown", "click"]) bar.addEventListener(ev, e => e.stopPropagation());     // a press on the bar is not a press on the chart
  bar.querySelector('[data-a="lock"]').addEventListener("click", () => { const m = o.list()[sel]; if (!m) return; m.locked = !m.locked; if (m.locked) sel = null; redraw(); o.changed(); });
  bar.querySelector('[data-a="del"]').addEventListener("click", () => { if (sel == null) return; o.list().splice(sel, 1); sel = null; redraw(); o.changed(); });
  function showBar() {
    const m = sel != null ? o.list()[sel] : null;
    bar.style.display = m && !held ? "flex" : "none";
    if (m) { const b = bar.querySelector('[data-a="lock"]'); b.textContent = m.locked ? "🔓 Unlock" : "🔒 Lock"; b.title = m.locked ? "let this mark be moved again" : "fix this mark in place: clicks go through it to what is underneath (Shift+click picks it up again)";
      bar.querySelector('[data-a="del"]').style.display = m.locked ? "none" : ""; }
  }
  function tag(g, text, x, y, color, bold) {
    g.font = (bold ? "bold 12px" : "11px") + " ui-monospace, Menlo, monospace";
    const w = g.measureText(text).width;
    const light = document.documentElement.dataset.theme === "light";         // a label sits on a small plate so it reads over candles, on either page colour
    g.fillStyle = light ? "rgba(255,255,255,.9)" : "rgba(0,0,0,.72)"; g.fillRect(x - 3, y - 8, w + 6, 16); g.fillStyle = color; g.fillText(text, x, y);
  }
  const lab = (g, text, x, y, color, right) => { g.font = "11px ui-monospace, Menlo, monospace"; tag(g, text, right ? x - g.measureText(text).width : x, y, color, false); };
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
      const dash = u.dash || [];                           // someone else's marks are dashed, so whose is whose shows without reading the label
      g.strokeStyle = g.fillStyle = u.color; g.lineWidth = 2; g.setLineDash(dash);
      let tx = Math.max(x0, 0) + 4, ty;
      if (u.shape === "vline") {
        g.setLineDash([6, 4]); g.beginPath(); g.moveTo(x0, 0); g.lineTo(x0, H); g.stroke(); g.setLineDash([]); tx = x0 + 6; ty = 44;      // under the chart's own legend in the corner
      } else if (u.shape === "line") {
        const y0 = yOf(u.p0), y1 = yOf(u.p1); if (y0 == null || y1 == null) continue;
        g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke(); if (MOVES.includes(u.kind)) arrowHead(g, x0, y0, x1, y1);
        g.setLineDash(dash); tx = (x0 + x1) / 2 + 6; ty = (y0 + y1) / 2;
      } else if (u.shape === "zone") {
        const a = yOf(u.top), b = yOf(u.bottom); if (a == null || b == null) continue;
        if (!u.nofill) { g.globalAlpha = .22; g.fillRect(x0, a, x1 - x0, b - a); g.globalAlpha = 1; }   // a far higher timeframe's zone: edges only
        g.strokeRect(x0, a, x1 - x0, b - a); ty = Math.min(a, b) - 9;
      } else {
        const y = yOf(u.price); if (y == null) continue;
        g.beginPath(); g.moveTo(x0, y); g.lineTo(x1, y); g.stroke(); ty = y - 9;
      }
      g.setLineDash([]); tag(g, u.label, tx, ty, u.color, true);
    }
    o.list().forEach((m, i) => {
      const x0 = m.t0 == null ? 0 : xOf(m.t0), x1 = xEnd(m), on = sel === i;
      if (x0 == null || x1 == null) return;
      g.strokeStyle = g.fillStyle = col(m); g.lineWidth = on ? 3 : 2; g.setLineDash([]);
      g.font = "11px ui-monospace, Menlo, monospace";
      const handles = [];
      if (m.shape === "vline") {
        g.setLineDash([6, 4]); g.beginPath(); g.moveTo(x0, 0); g.lineTo(x0, H); g.stroke(); g.setLineDash([]);
        lab(g, name(m), x0 + 6, 62, col(m)); handles.push([x0, 62]);
      } else if (m.shape === "line") {
        const y0 = yOf(m.p0), y1 = yOf(m.p1); if (y0 == null || y1 == null) return;
        if (m.kind === "fake push") g.setLineDash([6, 4]);
        g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
        if (MOVES.includes(m.kind)) arrowHead(g, x0, y0, x1, y1);
        lab(g, name(m), Math.min(x1, W - 90) + 6, y1, col(m)); handles.push([x0, y0], [x1, y1]);
      } else if (m.shape === "zone") {
        const a = yOf(m.top), b = yOf(m.bottom); if (a == null || b == null) return;
        g.globalAlpha = m.kind === "trading range" ? (on ? .10 : .04) : on ? .28 : .14; g.fillRect(x0, a, x1 - x0, b - a); g.globalAlpha = 1;      // a range is a frame, not a block
        g.beginPath(); g.moveTo(x0, a); g.lineTo(x1, a); g.moveTo(x0, b); g.lineTo(x1, b); g.stroke(); g.setLineDash([]);
        lab(g, name(m), Math.max(x0, 0) + 4, Math.min(a, b) - 9, col(m));
        handles.push([x0, a], [x1, a], [x0, b], [x1, b]);
      } else {
        const y = yOf(m.price); if (y == null) return;
        g.beginPath(); g.moveTo(x0, y); g.lineTo(x1, y); g.stroke();
        g.beginPath(); g.arc(x0, y, on ? 4 : 2.5, 0, 7); g.fill();
        lab(g, name(m), Math.min(x1, W) - 4, y + (m.side === "sellside" ? 10 : -10), col(m), true);
        handles.push([x0, y], [x1, y]);
      }
      g.strokeStyle = col(m); if (on) { g.setLineDash([]); g.fillStyle = o.color("--panel");
        for (const [x, y] of handles) { g.beginPath(); g.arc(x, y, 5, 0, 7); g.fill(); g.stroke(); } }
    });
    if (hover && (place || held)) {                     // the snapped point: a ring on the exact price
      g.setLineDash([]); g.lineWidth = 2; g.strokeStyle = o.color("--mine"); g.beginPath(); g.arc(hover.x, hover.y, 6, 0, 7); g.stroke();
      g.fillStyle = o.color("--mine"); g.beginPath(); g.arc(hover.x, hover.y, 2, 0, 7); g.fill();
    }
    g.restore(); showBar();
  }
  let alive = true;
  (function loop() { if (!alive) return; try { tick(); } catch (e) { /* chart not ready yet */ } requestAnimationFrame(loop); })();
  function tick() {
    const lr = ts.getVisibleLogicalRange();
    const s = [dirty, lr && lr.from, lr && lr.to, yOf(100), yOf(101), el.clientWidth, el.clientHeight, o.list().length, hover && hover.x, hover && hover.y, !!place].join("|");
    if (s !== sig) { sig = s; paint(); }
  }
  const redraw = () => { dirty++; };

  // ---- hit test + interaction
  function hit(px, py, locked) {                      // locked: also pick up locked marks (Shift+click)
    let best = null;
    const take = (i, part, d) => { if (!best || d < best.d) best = { i, part, d }; };
    o.list().forEach((m, i) => {
      if (m.locked && !locked) return;                  // a locked mark lets the press through to what is underneath
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
        const edge = Math.abs(py - a) <= G() + 2 ? "top" : Math.abs(py - b) <= G() + 2 ? "bottom" : null;
        if (end && edge) take(i, "c:" + end + ":" + edge, -1);                    // a corner: sizes the block both ways at once
        else if (end && py >= a - G() && py <= b + G()) take(i, end, 0);
        else if (Math.abs(py - a) <= G()) take(i, "top", Math.abs(py - a));
        else if (Math.abs(py - b) <= G()) take(i, "bottom", Math.abs(py - b));
        else if (py > a && py < b) take(i, "inside", G() + Math.min(1, Math.abs((x1 - x0) * (b - a)) / 1e7));      // of two blocks on top of each other, the smaller is picked up
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
    if (e.button !== 0 || bar.contains(e.target)) return;
    const pt = pos(e); if (!inPane(pt)) return;
    const [px, py] = pt, h = place ? null : hit(px, py, e.shiftKey), L = o.list();
    const [p, t] = h ? [pOfY(py), tOfX(px)] : point(px, py);
    if (h && L[h.i].locked) { sel = h.i; redraw(); e.preventDefault(); e.stopImmediatePropagation(); return; }     // picked up to unlock, not to move
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
    if (!held) {
      if (place && inPane([px, py])) { point(px, py); redraw(); } else if (hover) { hover = null; redraw(); }
      if (!place) {                                       // the pointer shows what a press here would do
        const h = inPane([px, py]) ? hit(px, py) : null, mk = h && o.list()[h.i], shown = ["move", "ns-resize", "ew-resize", "nwse-resize", "nesw-resize"].includes(el.style.cursor);
        const want = !h ? null : h.part.startsWith("c:") ? (["c:start:top", "c:end:bottom"].includes(h.part) ? "nwse-resize" : "nesw-resize")
          : ["top", "bottom"].includes(h.part) || (mk.shape === "level" && h.part === "body") ? "ns-resize" : ["start", "end"].includes(h.part) && mk.shape !== "line" ? "ew-resize" : "move";
        if (want) el.style.cursor = want; else if (shown) el.style.cursor = grab ? "grab" : "";
      }
      return; }
    if (Math.hypot(px - held.x0, py - held.y0) > 3) held.moved = true;
    if (!held.moved) return;
    const whole = ["inside", "body"].includes(held.part) && o.list()[held.i].shape !== "level";       // a whole mark being carried keeps its shape: no snapping
    let p, t; if (whole) { p = pOfY(py); t = tOfX(px); hover = null; } else [p, t] = point(px, py);
    if (p == null || t == null) return;
    const m = o.list()[held.i], q = held.orig, dp = r2(p - held.p0), dt = t - held.t0;
    if (m.shape === "vline") m.t0 = t;
    else if (m.shape === "line") {
      if (held.part === "end") { m.t1 = t; m.p1 = p; } else if (held.part === "start") { m.t0 = t; m.p0 = p; }
      else { m.p0 = r2(q.p0 + dp); m.p1 = r2(q.p1 + dp); m.t0 = q.t0 + dt; if (q.t1 != null) m.t1 = q.t1 + dt; }
    } else if (held.part === "end") m.t1 = t;
    else if (held.part === "start") m.t0 = t;
    else if (held.part.startsWith("c:")) {                                        // a corner handle: that side's time and that edge's price follow the mouse
      const [, side, edge] = held.part.split(":");
      if (side === "start") m.t0 = t; else m.t1 = t;
      m[edge] = p;
    }
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
    held = null; hover = null; freeze(false);
    redraw(); o.changed();                                                        // the page ends the placement: one placement per pick
  };
  const menu = e => { const [px, py] = pos(e), h = hit(px, py); if (h) { e.preventDefault(); o.list().splice(h.i, 1); sel = null; redraw(); o.changed(); }
    else if (hit(px, py, true)) e.preventDefault(); };      // a locked mark is not removed by a right-click
  const key = e => {
    if (["INPUT", "TEXTAREA", "SELECT"].includes(e.target.tagName)) return;
    if ((e.key === "Delete" || e.key === "Backspace") && sel != null && !(o.list()[sel] || {}).locked) { e.preventDefault(); o.list().splice(sel, 1); sel = null; redraw(); o.changed(); }
    else if (e.key === "Escape") { sel = null; redraw(); }
  };
  el.addEventListener("pointerdown", down, true);
  el.addEventListener("mousedown", e => { if (held && !bar.contains(e.target)) { e.preventDefault(); e.stopImmediatePropagation(); } }, true);
  window.addEventListener("pointermove", move); window.addEventListener("pointerup", up);
  // double-click a mark to lock it; double-click a locked mark to unlock it
  el.addEventListener("dblclick", e => {
    if (bar.contains(e.target)) return;
    const [px, py] = pos(e), h = hit(px, py, true); if (!h) return;
    const m = o.list()[h.i]; m.locked = !m.locked; sel = m.locked ? null : h.i;
    e.preventDefault(); e.stopImmediatePropagation(); redraw(); o.changed();
  }, true);
  el.addEventListener("contextmenu", menu); document.addEventListener("keydown", key);
  const destroy = () => { alive = false; window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up); document.removeEventListener("keydown", key); };
  return { redraw, setPlace, setGrab, grabbing: () => grab, deselect: () => { sel = null; redraw(); }, destroy };
}
