// Drag horizontal price lines and click-to-add on a lightweight-charts series (shared by liqmap.html / handling.html).
//   lineDrag(chart, series, el, {targets, move, done, click})
//     targets()          → [{key, price}] lines that may be dragged (a press within 7 px grabs the nearest)
//     move(key, price)   while dragging (redraw from your state); may return a new key to hold from now on
//     done(key, price)   on release
//     click(price)       a press + release that did not move (> 4 px) and did not grab a line; optional
// While a line is held the chart's own pan/zoom is switched off, so the drag never scrolls the chart.
function lineDrag(chart, series, el, opt) {
  const GRAB = 7, STILL = 4;
  let held = null, down = null;
  const y = e => e.clientY - el.getBoundingClientRect().top;
  const nearest = py => {
    let best = null;
    for (const t of opt.targets()) {
      const c = series.priceToCoordinate(t.price);
      if (c == null) continue;
      const d = Math.abs(c - py);
      if (d <= GRAB && (!best || d < best.d)) best = { ...t, d };
    }
    return best;
  };
  const price = py => { const p = series.coordinateToPrice(py); return p == null ? null : Math.round(p * 100) / 100; };
  const onDown = e => {
    if (e.button !== undefined && e.button !== 0) return;
    const py = y(e), hit = nearest(py);
    down = { x: e.clientX, y: e.clientY, py };
    if (hit) {
      held = hit.key;
      chart.applyOptions({ handleScroll: false, handleScale: false });
      e.stopPropagation(); e.preventDefault();
    }
  };
  const onMove = e => {
    if (held) {                       // move may hand back a new key (e.g. an engine line became your own copy)
      const p = price(y(e));
      if (p != null) { const nk = opt.move(held, p); if (typeof nk === "string") held = nk; }
      e.preventDefault(); return;
    }
    if (!down) el.style.cursor = nearest(y(e)) ? "ns-resize" : "";
  };
  const onUp = e => {
    if (held) {
      const p = price(y(e)), k = held; held = null;
      chart.applyOptions({ handleScroll: true, handleScale: true });
      if (p != null) opt.done(k, p);
      lineDrag.lastDrag = Date.now();
    } else if (down && opt.click && Math.hypot(e.clientX - down.x, e.clientY - down.y) <= STILL && el.contains(e.target)) {
      const p = price(down.py);
      if (p != null) opt.click(p);
    }
    down = null;
  };
  el.addEventListener("pointerdown", onDown, true);
  el.addEventListener("mousedown", e => { if (held) { e.stopPropagation(); e.preventDefault(); } }, true);
  el.addEventListener("touchstart", e => { if (held) e.stopPropagation(); }, true);
  window.addEventListener("pointermove", onMove);
  window.addEventListener("pointerup", onUp);
}
lineDrag.lastDrag = 0;
