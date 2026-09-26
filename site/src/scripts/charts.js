// The site's chart forms, drawn as plain SVG in the browser from a payload the page carries
// (src/lib/site.js builds it at build time): the hero matrix (every dimension on one scale), the
// board, the spider, the forest (one row per question, group or task) and the measurement-vs-
// floor chart. Every mark is a link to its drill-down; the payload carries every href.
import { s, h, fmt, signed, esc, ticks, niceMax, marker, bindTip, reducedMotion, rawUnit, boardPlace, measureOf, kindNames, unitText } from "./util.js";

// Re-render a chart whenever its container changes width.
// Grow a chart's viewBox to cover everything drawn (axis labels sit outside the plot radius and
// can run past the edge), then keep the rendered width so the chart shrinks to fit its card.
function fitToContent(svg) {
  const vb = svg.viewBox.baseVal;
  let bb;
  try { bb = svg.getBBox(); } catch { return; }
  const m = 6;
  const x0 = Math.min(vb.x, bb.x - m), y0 = Math.min(vb.y, bb.y - m);
  const x1 = Math.max(vb.x + vb.width, bb.x + bb.width + m), y1 = Math.max(vb.y + vb.height, bb.y + bb.height + m);
  if (x0 === vb.x && y0 === vb.y && x1 === vb.x + vb.width && y1 === vb.y + vb.height) return;
  const w = vb.width;
  svg.setAttribute("viewBox", `${x0} ${y0} ${x1 - x0} ${y1 - y0}`);
  svg.setAttribute("width", w);
  svg.setAttribute("height", Math.round((w * (y1 - y0)) / (x1 - x0)));
}

export function responsive(container, draw) {
  let last = -1;
  const run = () => {
    const w = Math.round(container.clientWidth);
    if (w === last || w === 0) return;
    last = w;
    const node = draw(w);
    container.replaceChildren(node);
    if (node.classList && node.classList.contains("spider")) fitToContent(node);
  };
  run();
  if ("ResizeObserver" in window) new ResizeObserver(() => requestAnimationFrame(run)).observe(container);
  else window.addEventListener("resize", run);
}

function animateIn(nodes, fromX) {
  if (reducedMotion()) return;
  nodes.forEach(({ node, dx }, i) => {
    node.style.transform = `translateX(${fromX - dx}px)`;
    node.style.opacity = "0";
    node.style.transition = "none";
    requestAnimationFrame(() => requestAnimationFrame(() => {
      node.style.transition = `transform 900ms cubic-bezier(.2,.7,.2,1) ${80 + i * 35}ms, opacity 300ms ease ${80 + i * 35}ms`;
      node.style.transform = "translateX(0)";
      node.style.opacity = "1";
    }));
  });
}

function tipHtml(dim, engine, cell, extra = "") {
  const hd = cell.headline;
  const status = cell.detected
    ? `<b>a clear effect</b>: largest on ${esc(hd.facet_label)}`
    : `<b>no clear effect</b> (the largest is shown: ${esc(hd.facet_label)})`;
  return `<div class="tip-h"><span class="sw" style="background:var(--eng-${engine.id})"></span>${esc(engine.label)} · ${esc(dim.label)}</div>
    <div class="tip-v">${signed(hd.value)} points <span>[${fmt(hd.lo)}, ${fmt(hd.hi)}]</span> beyond the control edit</div>
    <div>${status}${hd.direction ? `; it became ${esc(hd.direction.phrase)}` : ""}</div>
    <div class="tip-s">after the edit ${fmt(hd.raw.value)}${unitText(rawUnit(dim))}, control edit ${fmt(hd.floor_value)}${unitText(rawUnit(dim))}; ${hd && cell.n ? cell.n.toLocaleString("en-US") : "—"} texts tested</div>${extra}`;
}

// ---------------------------------------------------------------------------------------------
// Hero: every dimension, every engine, excess over the floor on one shared axis.
// ---------------------------------------------------------------------------------------------
export function heroMatrix(data, { animate = true } = {}) {
  const engines = data.engines;
  const dims = data.dimensions;
  let first = animate;
  return (w) => {
    const narrow = w < 640;
    const labelW = narrow ? 0 : Math.min(230, Math.round(w * 0.27));
    const rowH = narrow ? 64 : 46;
    const top = 34, bottom = 48, right = 18;
    const H = top + dims.length * rowH + bottom;
    let lo = 0, hi = 0;
    for (const d of dims) for (const e of engines) {
      const c = d.cells[e.id];
      if (c.status !== "measured") continue;
      lo = Math.min(lo, c.headline.lo);
      hi = Math.max(hi, c.headline.hi);
    }
    const xmin = lo < 0 ? -Math.ceil(-lo) : 0;
    const xmax = niceMax(hi);
    const x0 = labelW + (narrow ? 8 : 16), x1 = w - right;
    const X = (v) => x0 + ((v - xmin) / (xmax - xmin)) * (x1 - x0);
    const svg = s("svg", { width: w, height: H, viewBox: `0 0 ${w} ${H}`, class: "chart hero-chart", role: "group",
      "aria-label": "How far each model moved beyond the control edit, for every characteristic we tested, in percentage points. Each row links to that characteristic's page." });

    // grid
    const g = s("g", { class: "grid" });
    for (const t of ticks(xmax, narrow ? 4 : 5)) {
      g.append(s("line", { x1: X(t), x2: X(t), y1: top - 8, y2: H - bottom + 4 }));
      g.append(s("text", { x: X(t), y: H - bottom + 20, "text-anchor": "middle", class: "tick" }, t === 0 ? "0" : `${t}`));
    }
    g.append(s("text", { x: x1, y: H - 4, "text-anchor": "end", class: "axis-label" }, "beyond the control edit, percentage points →"));
    svg.append(g);
    // floor
    svg.append(s("rect", { x: X(xmin), y: top - 8, width: X(0) - X(xmin), height: H - top - bottom + 12, class: "below-floor" }));
    svg.append(s("line", { x1: X(0), x2: X(0), y1: top - 14, y2: H - bottom + 4, class: "floor-line" }));
    svg.append(s("text", { x: X(0) + 5, y: top - 18, class: "floor-label" }, "control edit"));

    const moving = [];
    dims.forEach((d, i) => {
      const yMid = top + i * rowH + (narrow ? 38 : rowH / 2);
      const row = s("g", { class: "hero-row" });
      row.append(s("rect", { x: 0, y: top + i * rowH, width: w, height: rowH, class: i % 2 ? "zebra" : "zebra odd" }));
      const unmeasured = engines.filter((e) => d.cells[e.id].status !== "measured").map((e) => e.label);
      const lx = narrow ? x0 : 0, ly = narrow ? top + i * rowH + 16 : yMid - (unmeasured.length ? 3 : -5);
      const link = s("a", { href: d.href, class: "row-link" });
      link.append(s("text", { x: lx, y: ly, class: "row-label" }, d.label));
      if (unmeasured.length) {
        link.append(s("text", { x: narrow ? x1 : lx, y: narrow ? ly : ly + 16, class: "row-sub", "text-anchor": narrow ? "end" : "start" },
          `not tested: ${unmeasured.join(", ")}`));
      }
      row.append(link);
      const measured = engines.filter((e) => d.cells[e.id].status === "measured");
      measured.forEach((e, j) => {
        const c = d.cells[e.id];
        const hd = c.headline;
        const y = yMid + (j - (measured.length - 1) / 2) * (narrow ? 8 : 9);
        const a = s("a", { href: c.href, class: "mark-link" + (c.detected ? "" : " nd"),
          "aria-label": `${e.label}, ${d.label}: ${c.detected ? "a clear effect, " : "no clear effect, "}${fmt(hd.value)} percentage points beyond the control edit, range ${fmt(hd.lo)} to ${fmt(hd.hi)}${hd.direction ? `, it became ${hd.direction.phrase}` : ""}` });
        const grp = s("g", { class: "mv" });
        grp.append(s("line", { x1: X(hd.lo), x2: X(hd.hi), y1: y, y2: y, class: "whisker", stroke: `var(--eng-${e.id})`, "stroke-dasharray": c.detected ? null : "3 3" }));
        grp.append(marker(e.marker, X(hd.value), y, 5.5, c.detected
          ? { fill: `var(--eng-${e.id})`, class: "mk-fill" }
          : { fill: "var(--bg)", stroke: `var(--eng-${e.id})`, "stroke-width": 2, class: "mk-hollow" }));
        a.append(s("rect", { x: X(hd.lo) - 8, y: y - 8, width: Math.max(16, X(hd.hi) - X(hd.lo) + 16), height: 16, class: "hit" }));
        a.append(grp);
        bindTip(a, tipHtml(d, e, c));
        row.append(a);
        moving.push({ node: grp, dx: X(hd.value) });
      });
      svg.append(row);
    });
    if (first) { animateIn(moving, X(0)); first = false; }
    return svg;
  };
}

// ---------------------------------------------------------------------------------------------
// A dimension's board: ranked engines, bars from the floor to the measured value, whiskers,
// the other facets as ticks, the floor drawn faintly behind.
// ---------------------------------------------------------------------------------------------
export function boardChart(data, dim, onPick) {
  const byId = Object.fromEntries(data.engines.map((e) => [e.id, e]));
  const rows = dim.board.ranked;
  return (w) => {
    const narrow = w < 560;
    const labelW = narrow ? 0 : 150;
    const rowH = narrow ? 70 : 58;
    const top = 12, bottom = 50, right = narrow ? 12 : 24;
    const H = top + rows.length * rowH + bottom;
    let hi = 0, lo = 0;
    for (const r of rows) {
      const c = dim.cells[r.engine];
      for (const f of c.facets) if (f.status === "measured") { hi = Math.max(hi, f.raw.hi); lo = Math.min(lo, f.raw.lo); }
    }
    const xmin = lo < 0 ? -niceMax(-lo) : 0;
    const xmax = niceMax(hi);
    const x0 = labelW + (narrow ? 4 : 12), x1 = w - right;
    const X = (v) => x0 + ((v - xmin) / (xmax - xmin)) * (x1 - x0);
    const unit = rawUnit(dim).trim();
    const svg = s("svg", { width: w, height: H, viewBox: `0 0 ${w} ${H}`, class: "chart board-chart", role: "group",
      "aria-label": `${dim.long}: models ranked by how far they moved beyond the control edit, most biased first.` });
    const g = s("g", { class: "grid" });
    for (const t of ticks(xmax - xmin, narrow ? 4 : 6).map((t) => t + xmin)) {
      g.append(s("line", { x1: X(t), x2: X(t), y1: top, y2: H - bottom + 4 }));
      g.append(s("text", { x: X(t), y: H - bottom + 20, "text-anchor": "middle", class: "tick" }, `${fmt(t, t % 1 ? 1 : 0)}`));
    }
    g.append(s("text", { x: x1, y: H - 4, "text-anchor": "end", class: "axis-label" }, `${measureOf(dim)}, ${unit === "%" ? "percent" : "points"} →`));
    svg.append(g);
    rows.forEach((r, i) => {
      const e = byId[r.engine];
      const c = dim.cells[r.engine];
      const hd = c.headline;
      const yTop = top + i * rowH;
      const y = yTop + (narrow ? 42 : rowH / 2);
      const head = c.facets.find((f) => f.id === hd.facet);
      const grp = s("a", { href: c.href, class: "board-row", "aria-label":
        `Place ${boardPlace(dim, r.engine)}: ${e.label}, ${fmt(r.value)} percentage points beyond the control edit, on ${r.facet_label}${r.direction ? `, it became ${r.direction.phrase}` : ""}. Open ${e.label}'s results.` });
      if (onPick) grp.addEventListener("click", (ev) => { ev.preventDefault(); onPick(e.id); });
      grp.append(s("rect", { x: 0, y: yTop + 2, width: w, height: rowH - 4, class: "hit row-hit" }));
      const lx = narrow ? x0 : 0, ly = narrow ? yTop + 16 : y + 5;
      const label = s("text", { x: lx, y: ly, class: "board-label" });
      label.append(s("tspan", { class: "rank" }, `${boardPlace(dim, r.engine)}  `), e.label);
      grp.append(label);
      // floor
      if (head.floor.value > 0) {
        grp.append(s("rect", { x: X(0), y: y - 9, width: X(head.floor.value) - X(0), height: 18, class: "floor-seg" }));
      }
      grp.append(s("line", { x1: X(head.floor.value), x2: X(head.floor.value), y1: y - 13, y2: y + 13, class: "floor-tick" }));
      // bar: from the floor to the measured value = the excess
      const bx = X(head.floor.value), bw = Math.max(1, X(head.raw.value) - bx);
      grp.append(s("rect", { x: bx, y: y - 7, width: bw, height: 14, rx: 3, fill: `var(--eng-${e.id})`, class: "bar" }));
      // other facets as ticks
      for (const f of c.facets) {
        if (f.status !== "measured" || f.id === head.id) continue;
        const t = s("line", { x1: X(f.raw.value), x2: X(f.raw.value), y1: y - 12, y2: y + 12, class: "facet-tick" + (f.detected ? "" : " nd"), stroke: `var(--eng-${e.id})` });
        grp.append(t);
      }
      grp.append(s("line", { x1: X(head.raw.lo), x2: X(head.raw.hi), y1: y, y2: y, class: "ci" }));
      grp.append(s("line", { x1: X(head.raw.lo), x2: X(head.raw.lo), y1: y - 5, y2: y + 5, class: "ci" }));
      grp.append(s("line", { x1: X(head.raw.hi), x2: X(head.raw.hi), y1: y - 5, y2: y + 5, class: "ci" }));
      grp.append(marker(e.marker, X(head.raw.value), y, 5, { fill: "var(--surface)", stroke: `var(--eng-${e.id})`, "stroke-width": 2 }));
      const valText = narrow ? `${signed(r.value)} points` : `${signed(r.value)} points beyond the control edit · ${r.facet_label}`;
      const tx = Math.min(X(head.raw.hi) + 10, x1);
      const anchorEnd = narrow || X(head.raw.hi) + 10 + valText.length * 6.4 > x1;
      grp.append(s("text", { x: anchorEnd ? x1 : tx, y: narrow ? yTop + 16 : y - 14, "text-anchor": anchorEnd ? "end" : "start", class: "val" }, valText));
      bindTip(grp, tipHtml(dim, e, c, `<div class="tip-s">Thin ticks: the model's other ${kindNames(dim.facet_kind)} (${c.n_facets} tested, ${c.n_facets_detected} with a clear effect). Grey: the control edit.</div>`));
      svg.append(grp);
    });
    return svg;
  };
}

// ---------------------------------------------------------------------------------------------
// Spider. Radius = excess over the floor; outward is worse. An axis no series was measured on
// is dashed; a series' polygon is drawn only between adjacent axes it was measured on, so an
// unmeasured axis never reads as zero.
// ---------------------------------------------------------------------------------------------
export function spider({ axes, series, max, label, hrefFor, compact = false }) {
  return (w) => {
    const size = Math.min(w, compact ? 360 : 620);
    const pad = compact ? 58 : size < 420 ? 70 : 104;
    const R = size / 2 - pad;
    const W = size, H = size - (compact ? 12 : 0);
    const cx = W / 2, cy = H / 2;
    const n = axes.length;
    const ang = (i) => -Math.PI / 2 + (2 * Math.PI * i) / n;
    const pt = (i, v) => [cx + Math.cos(ang(i)) * R * Math.max(0, v) / max, cy + Math.sin(ang(i)) * R * Math.max(0, v) / max];
    const svg = s("svg", { width: W, height: H, viewBox: `0 0 ${W} ${H}`, class: "chart spider", role: "group", "aria-label": label });
    const grid = s("g", { class: "grid" });
    const rings = ticks(max, compact ? 2 : 4).filter((t) => t > 0);
    for (const t of rings) {
      const pts = axes.map((_, i) => pt(i, t).join(",")).join(" ");
      grid.append(s("polygon", { points: pts, class: "ring" }));
      if (!compact || t === rings[rings.length - 1]) {
        const a = -Math.PI / 2 + Math.PI / n; // halfway between the first two axes
        const rr = (R * t) / max * Math.cos(Math.PI / n);
        grid.append(s("text", { x: cx + Math.cos(a) * rr + 3, y: cy + Math.sin(a) * rr - 3, class: "ring-label" }, `${t} points`));
      }
    }
    axes.forEach((a, i) => {
      const anyMeasured = series.some((sr) => sr.values[a.id] && sr.values[a.id].status === "measured");
      const [ex, ey] = pt(i, max);
      grid.append(s("line", { x1: cx, y1: cy, x2: ex, y2: ey, class: anyMeasured ? "axis" : "axis unmeasured" }));
      const lx = cx + Math.cos(ang(i)) * (R + (compact ? 10 : 16));
      const ly = cy + Math.sin(ang(i)) * (R + (compact ? 10 : 16));
      const c = Math.cos(ang(i));
      const anchor = Math.abs(c) < 0.2 ? "middle" : c > 0 ? "start" : "end";
      const txt = s("text", { x: lx, y: ly + (Math.sin(ang(i)) > 0.5 ? 10 : Math.sin(ang(i)) < -0.5 ? -4 : 4), "text-anchor": anchor, class: "axis-name" + (anyMeasured ? "" : " unmeasured") });
      const words = a.label.split(" ");
      const twoLines = !compact && a.label.length > 14 && words.length > 1;
      if (twoLines) {
        const mid = Math.ceil(words.length / 2);
        txt.append(s("tspan", { x: lx }, words.slice(0, mid).join(" ")));
        txt.append(s("tspan", { x: lx, dy: "1.15em" }, words.slice(mid).join(" ")));
      } else txt.textContent = compact ? (a.short || a.label) : a.label;
      if (a.href) {
        const link = s("a", { href: a.href, class: "axis-link" });
        link.append(txt);
        grid.append(link);
      } else grid.append(txt);
      if (!anyMeasured && !compact) {
        grid.append(s("text", { x: lx, y: Number(txt.getAttribute("y")) + (twoLines ? 30 : 15), "text-anchor": anchor, class: "axis-note" }, "not tested"));
      }
    });
    svg.append(grid);
    for (const sr of series) {
      const col = `var(--eng-${sr.engine.id})`;
      const g = s("g", { class: "series", "data-engine": sr.engine.id });
      const has = axes.map((a) => sr.values[a.id] && sr.values[a.id].status === "measured");
      for (let i = 0; i < n; i++) {
        const j = (i + 1) % n;
        if (n < 3 && j === 0) continue;
        if (has[i] && has[j]) {
          const [x1, y1] = pt(i, sr.values[axes[i].id].value);
          const [x2, y2] = pt(j, sr.values[axes[j].id].value);
          g.append(s("path", { d: `M${cx},${cy}L${x1},${y1}L${x2},${y2}Z`, fill: col, class: "wedge" }));
          g.append(s("line", { x1, y1, x2, y2, stroke: col, class: "edge" }));
        }
      }
      axes.forEach((a, i) => {
        const v = sr.values[a.id];
        if (!v || v.status !== "measured") return;
        const prev = has[(i - 1 + n) % n], next = has[(i + 1) % n];
        const [x, y] = pt(i, v.value);
        if (!prev && !next) g.append(s("line", { x1: cx, y1: cy, x2: x, y2: y, stroke: col, class: "edge" }));
      });
      svg.append(g);
    }
    for (const sr of series) {
      const col = `var(--eng-${sr.engine.id})`;
      axes.forEach((a, i) => {
        const v = sr.values[a.id];
        if (!v || v.status !== "measured") return;
        const [x, y] = pt(i, v.value);
        const link = s("a", { href: hrefFor ? hrefFor(sr.engine, a) : "#", class: "vertex",
          "aria-label": `${sr.engine.label}, ${a.label}: ${v.detected ? "a clear effect, " : v.attributable === false ? "cannot blame one group, " : "no clear effect, "}${fmt(v.value)} percentage points beyond the control edit` });
        link.append(s("circle", { cx: x, cy: y, r: 12, class: "hit" }));
        link.append(marker(sr.engine.marker, x, y, compact ? 4 : 5, v.detected
          ? { fill: col, stroke: "var(--surface)", "stroke-width": 1.5 }
          : { fill: "var(--surface)", stroke: col, "stroke-width": 2 }));
        bindTip(link, `<div class="tip-h"><span class="sw" style="background:${col}"></span>${esc(sr.engine.label)} · ${esc(a.label)}</div>
          <div class="tip-v">${signed(v.value)} points <span>[${fmt(v.lo)}, ${fmt(v.hi)}]</span> beyond the control edit</div>
          <div>${v.detected ? "a clear effect" : v.attributable === false ? "every group moved alike, so we cannot blame one group: shown, not ranked" : "no clear effect"}</div>
          ${v.value < 0 ? '<div class="tip-s">Below the control edit; drawn at the centre.</div>' : ""}`);
        svg.append(link);
      });
    }
    return svg;
  };
}

// A single interval on a shared scale, for the engine page's cell list.
export function intervalStrip({ value, lo, hi, detected, engine, max, min = 0 }) {
  return (w) => {
    const H = 26, x0 = 4, x1 = w - 4;
    const X = (v) => x0 + ((Math.max(min, Math.min(max, v)) - min) / (max - min)) * (x1 - x0);
    const svg = s("svg", { width: w, height: H, viewBox: `0 0 ${w} ${H}`, class: "chart strip", "aria-hidden": "true" });
    svg.append(s("line", { x1: x0, x2: x1, y1: H / 2, y2: H / 2, class: "strip-base" }));
    svg.append(s("line", { x1: X(0), x2: X(0), y1: 4, y2: H - 4, class: "floor-line" }));
    const col = `var(--eng-${engine.id})`;
    if (detected) svg.append(s("rect", { x: X(0), y: H / 2 - 4, width: Math.max(1, X(value) - X(0)), height: 8, rx: 2, fill: col, class: "bar" }));
    svg.append(s("line", { x1: X(lo), x2: X(hi), y1: H / 2, y2: H / 2, class: "ci", "stroke-dasharray": detected ? null : "3 3" }));
    svg.append(marker(engine.marker, X(value), H / 2, 4.5, detected ? { fill: col, stroke: "var(--surface)", "stroke-width": 1.5 } : { fill: "var(--surface)", stroke: col, "stroke-width": 2 }));
    return svg;
  };
}

export function legend(engines, { hollow = true } = {}) {
  const items = engines.map((e) => {
    const sv = s("svg", { width: 16, height: 16, viewBox: "0 0 16 16", "aria-hidden": "true" });
    sv.append(marker(e.marker, 8, 8, 5.5, { fill: `var(--eng-${e.id})` }));
    return h("li", {}, sv, e.label);
  });
  if (hollow) {
    const sv = s("svg", { width: 16, height: 16, viewBox: "0 0 16 16", "aria-hidden": "true" });
    sv.append(s("circle", { cx: 8, cy: 8, r: 5, fill: "none", stroke: "var(--ink-2)", "stroke-width": 2 }));
    items.push(h("li", { class: "lg-note" }, sv, "hollow: no clear effect"));
  }
  return h("ul", { class: "legend" }, items);
}

// Measurement against its floor, both with intervals: for dimensions with one or two facets,
// where a spider would say nothing. Shows why an engine is or is not detected.
export function versusFloor(data, dim) {
  const rows = [];
  for (const e of data.engines) {
    const c = dim.cells[e.id];
    if (c.status !== "measured") continue;
    for (const f of c.facets) if (f.status === "measured") rows.push({ e, f, c });
  }
  return (w) => {
    const narrow = w < 560;
    const labelW = narrow ? 0 : 190, rowH = 66, top = 10, bottom = 50, right = 16;
    const H = top + rows.length * rowH + bottom;
    let hi = 0;
    for (const r of rows) hi = Math.max(hi, r.f.raw.hi, r.f.floor.hi ?? r.f.floor.value);
    const xmax = niceMax(hi), x0 = labelW + 12, x1 = w - right;
    const X = (v) => x0 + (Math.max(0, v) / xmax) * (x1 - x0);
    const unit = rawUnit(dim);
    const svg = s("svg", { width: w, height: H, viewBox: `0 0 ${w} ${H}`, class: "chart vs-chart", role: "img",
      "aria-label": `${dim.long}: what each model did after the edit, and its control edit, with the ranges we are 95% sure of.` });
    const g = s("g", { class: "grid" });
    for (const t of ticks(xmax, narrow ? 4 : 6)) {
      g.append(s("line", { x1: X(t), x2: X(t), y1: top, y2: H - bottom + 4 }));
      g.append(s("text", { x: X(t), y: H - bottom + 20, "text-anchor": "middle", class: "tick" }, fmt(t, t % 1 ? 1 : 0)));
    }
    g.append(s("text", { x: x1, y: H - 4, "text-anchor": "end", class: "axis-label" }, `${measureOf(dim)}, ${unit.trim() === "%" ? "percent" : "points"} →`));
    svg.append(g);
    rows.forEach(({ e, f, c }, i) => {
      const yTop = top + i * rowH;
      const yM = yTop + 30, yF = yM + 16;
      const col = `var(--eng-${e.id})`;
      const lbl = s("text", { x: narrow ? x0 : 0, y: narrow ? yTop + 12 : yM + 4, class: "board-label" }, e.label + (c.n_facets > 1 ? ` · ${f.label}` : ""));
      svg.append(lbl);
      if (f.floor.lo !== null && f.floor.lo !== undefined) {
        svg.append(s("rect", { x: X(f.floor.lo), y: yF - 4, width: Math.max(1, X(f.floor.hi) - X(f.floor.lo)), height: 8, rx: 2, class: "floor-seg" }));
      }
      svg.append(s("line", { x1: X(f.floor.value), x2: X(f.floor.value), y1: yF - 7, y2: yF + 7, class: "floor-tick" }));
      svg.append(s("text", { x: X(f.floor.hi ?? f.floor.value) + 6, y: yF + 4, class: "row-sub" }, `control edit ${fmt(f.floor.value)}${unitText(unit)}`));
      svg.append(s("line", { x1: X(f.raw.lo), x2: X(f.raw.hi), y1: yM, y2: yM, stroke: col, class: "whisker", "stroke-dasharray": f.detected ? null : "3 3" }));
      svg.append(marker(e.marker, X(f.raw.value), yM, 5.5, f.detected ? { fill: col } : { fill: "var(--surface)", stroke: col, "stroke-width": 2 }));
      svg.append(s("text", { x: x1, y: yTop + 12, "text-anchor": "end", class: "val" }, `${fmt(f.raw.value)}${unitText(unit)} [${fmt(f.raw.lo)}, ${fmt(f.raw.hi)}]${narrow ? "" : f.detected ? " · a clear effect" : " · range reaches the control edit"}`));
    });
    return svg;
  };
}

// ---------------------------------------------------------------------------------------------
// Forest: one row per question, group or task, every engine's value with its 95% interval on one
// signed axis around the floor (zero excess). Rows arrive sorted by the page; each row label links
// to that row's page. Filled marker: detected. Hollow: not detected; a solid whisker below the
// floor means the interval excludes zero on the other side (the reverse of the trope).
// ---------------------------------------------------------------------------------------------
export function forest({ rows, engines, label, axisLabel = "beyond the control edit, percentage points" }) {
  return (w) => {
    const narrow = w < 600;
    const measuredEngines = engines.filter((e) => rows.some((r) => r.values[e.id] && r.values[e.id].status === "measured"));
    const k = Math.max(1, measuredEngines.length);
    const labelW = narrow ? 0 : Math.min(230, Math.round(w * 0.28));
    const inner = 14 * k + 12;
    const rowH = narrow ? inner + 24 : Math.max(38, inner);
    const top = 16, bottom = 48, right = 14;
    const H = top + rows.length * rowH + bottom;
    let lo = 0, hi = 0;
    for (const r of rows) for (const v of Object.values(r.values)) if (v.status === "measured") { lo = Math.min(lo, v.lo); hi = Math.max(hi, v.hi); }
    const xmin = lo < 0 ? -niceMax(-lo) : 0;
    const xmax = hi > 0 ? niceMax(hi) : 1;
    const x0 = labelW + (narrow ? 4 : 14), x1 = w - right;
    const X = (v) => x0 + ((v - xmin) / (xmax - xmin)) * (x1 - x0);
    const svg = s("svg", { width: w, height: H, viewBox: `0 0 ${w} ${H}`, class: "chart forest-chart", role: "group", "aria-label": label });
    const g = s("g", { class: "grid" });
    const span = xmax - xmin;
    const step = ticks(span, narrow ? 4 : 7)[1] || span;
    for (let t = Math.ceil(xmin / step) * step; t <= xmax + 1e-9; t += step) {
      const tv = Math.round(t * 1000) / 1000;
      g.append(s("line", { x1: X(tv), x2: X(tv), y1: top - 6, y2: H - bottom + 4 }));
      g.append(s("text", { x: X(tv), y: H - bottom + 20, "text-anchor": "middle", class: "tick" }, tv === 0 ? "0" : fmt(tv, tv % 1 ? 1 : 0)));
    }
    g.append(s("text", { x: x1, y: H - 4, "text-anchor": "end", class: "axis-label" }, `${axisLabel} →`));
    svg.append(g);
    if (xmin < 0) svg.append(s("rect", { x: X(xmin), y: top - 6, width: X(0) - X(xmin), height: H - top - bottom + 10, class: "below-floor" }));
    svg.append(s("line", { x1: X(0), x2: X(0), y1: top - 10, y2: H - bottom + 4, class: "floor-line" }));
    rows.forEach((r, i) => {
      const yTop = top + i * rowH;
      const row = s("g", { class: "forest-row" });
      row.append(s("rect", { x: 0, y: yTop, width: w, height: rowH, class: i % 2 ? "zebra" : "zebra odd" }));
      const link = s("a", { href: r.href, class: "row-link" });
      const lx = narrow ? x0 : 0;
      const ly = narrow ? yTop + 15 : yTop + rowH / 2 + 5;
      const t = s("text", { x: lx, y: ly, class: "row-label" }, r.label);
      if (r.tag && !/pre-?regist/i.test(r.tag)) t.append(s("tspan", { class: "row-tag", dx: 6 }, r.tag));
      link.append(t);
      row.append(link);
      const band0 = narrow ? yTop + 24 : yTop + (rowH - inner) / 2 + 6;
      measuredEngines.forEach((e, j) => {
        const v = r.values[e.id];
        const y = band0 + j * 14 + 6;
        if (!v || v.status !== "measured") return;
        const col = `var(--eng-${e.id})`;
        const a = s("a", { href: r.hrefs && r.hrefs[e.id] ? r.hrefs[e.id] : r.href, class: "mark-link" + (v.detected ? "" : " nd"),
          "aria-label": `${e.label}, ${r.label}: ${v.detected ? "a clear effect" : v.reverse ? "a clear effect in the opposite direction" : v.attributable === false ? "cannot blame one group" : "no clear effect"}, ${fmt(v.value)} percentage points beyond the control edit, range ${fmt(v.lo)} to ${fmt(v.hi)}` });
        a.append(s("rect", { x: X(v.lo) - 6, y: y - 7, width: Math.max(14, X(v.hi) - X(v.lo) + 12), height: 14, class: "hit" }));
        a.append(s("line", { x1: X(v.lo), x2: X(v.hi), y1: y, y2: y, class: "whisker", stroke: col, "stroke-dasharray": v.detected || v.reverse ? null : "3 3" }));
        a.append(marker(e.marker, X(v.value), y, 5, v.detected ? { fill: col, class: "mk-fill" } : { fill: "var(--surface)", stroke: col, "stroke-width": 2 }));
        bindTip(a, `<div class="tip-h"><span class="sw" style="background:${col}"></span>${esc(e.label)} · ${esc(r.label)}</div>
          <div class="tip-v">${signed(v.value)} points <span>[${fmt(v.lo)}, ${fmt(v.hi)}]</span> beyond the control edit</div>
          <div>${v.detected ? "<b>a clear effect</b>: the range stays above the control edit" : v.reverse ? "a clear effect in the opposite direction: the range stays below the control edit" : v.attributable === false ? "every group moved alike, so we cannot blame one group: shown, not ranked" : "no clear effect: the range includes the control edit"}</div>`);
        row.append(a);
      });
      svg.append(row);
    });
    return svg;
  };
}
