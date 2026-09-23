// Small DOM, SVG and formatting helpers. No dependencies.

export const SVG_NS = "http://www.w3.org/2000/svg";

export function h(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  setAttrs(node, attrs);
  append(node, children);
  return node;
}

export function s(tag, attrs = {}, ...children) {
  const node = document.createElementNS(SVG_NS, tag);
  setAttrs(node, attrs);
  append(node, children);
  return node;
}

function setAttrs(node, attrs) {
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") node.setAttribute("class", v);
    else if (k === "text") node.textContent = v;
    else if (k === "html") node.innerHTML = v;
    else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
    else if (k === "dataset") Object.assign(node.dataset, v);
    else node.setAttribute(k, v === true ? "" : v);
  }
}

function append(node, children) {
  for (const c of children.flat(Infinity)) {
    if (c === null || c === undefined || c === false) continue;
    node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
}

export function fmt(x, digits = 2) {
  if (x === null || x === undefined || Number.isNaN(x)) return "—";
  const v = Number(x).toFixed(digits);
  return v === "-0.00" ? "0.00" : v.replace("-", "−");
}

export function signed(x, digits = 2) {
  if (x === null || x === undefined) return "—";
  return (x > 0 ? "+" : "") + fmt(x, digits);
}

export function int(n) {
  return n === null || n === undefined ? "—" : Number(n).toLocaleString("en-US");
}

// The unit a dimension's raw measurement is reported in.
export function rawUnit(dim) {
  return dim.raw_unit || " pts";
}

export function rawText(dim, raw) {
  return `${fmt(raw.value)}${rawUnit(dim)} [${fmt(raw.lo)}, ${fmt(raw.hi)}]`;
}

export function excessText(e) {
  return `${signed(e.value)} pp [${fmt(e.lo)}, ${fmt(e.hi)}]`;
}

export function rankText(r) {
  if (r === null || r === undefined) return "—";
  return Number.isInteger(r) ? String(r) : r.toFixed(1);
}

export function niceMax(v) {
  if (v <= 0) return 1;
  const pow = Math.pow(10, Math.floor(Math.log10(v)));
  for (const m of [1, 2, 2.5, 5, 10]) if (m * pow >= v) return m * pow;
  return 10 * pow;
}

export function ticks(max, target = 5) {
  const raw = max / target;
  const pow = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * pow).find((st) => st >= raw) || raw;
  const out = [];
  for (let t = 0; t <= max + 1e-9; t += step) out.push(Math.round(t * 1000) / 1000);
  return out;
}

export function qs(name) {
  return new URLSearchParams(window.location.search).get(name);
}

export const reducedMotion = () =>
  window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// Marker shapes per engine: colour is never the only channel.
export function marker(shape, cx, cy, r, attrs = {}) {
  if (shape === "square") {
    const a = r * 0.9;
    return s("rect", { x: cx - a, y: cy - a, width: 2 * a, height: 2 * a, rx: 1.5, ...attrs });
  }
  if (shape === "diamond") {
    const a = r * 1.25;
    return s("path", { d: `M${cx},${cy - a}L${cx + a},${cy}L${cx},${cy + a}L${cx - a},${cy}Z`, ...attrs });
  }
  return s("circle", { cx, cy, r, ...attrs });
}

export function markerIcon(engine, size = 14) {
  const svg = s("svg", { width: size, height: size, viewBox: "0 0 14 14", "aria-hidden": "true", class: "mk" });
  svg.append(marker(engine.marker, 7, 7, 5, { fill: `var(--eng-${engine.id})` }));
  return svg;
}

// One shared tooltip, shown on hover and on keyboard focus.
let tip;
export function tooltip() {
  if (!tip) {
    tip = h("div", { class: "tip", role: "tooltip", "aria-hidden": "true" });
    document.body.append(tip);
  }
  return tip;
}

export function bindTip(node, html) {
  const show = (ev) => {
    const t = tooltip();
    t.innerHTML = html;
    t.classList.add("on");
    place(ev);
  };
  const place = (ev) => {
    const t = tooltip();
    let x, y;
    if (ev && ev.clientX !== undefined && ev.type.startsWith("mouse")) {
      x = ev.clientX; y = ev.clientY;
    } else {
      const r = node.getBoundingClientRect();
      x = r.left + r.width / 2; y = r.top;
    }
    const w = t.offsetWidth, hgt = t.offsetHeight;
    const left = Math.min(Math.max(8, x - w / 2), window.innerWidth - w - 8);
    const top = y - hgt - 14 < 8 ? y + 18 : y - hgt - 14;
    t.style.transform = `translate(${Math.round(left)}px, ${Math.round(top)}px)`;
  };
  const hide = () => tooltip().classList.remove("on");
  node.addEventListener("mouseenter", show);
  node.addEventListener("mousemove", place);
  node.addEventListener("mouseleave", hide);
  node.addEventListener("focus", show);
  node.addEventListener("blur", hide);
}

export function esc(str) {
  return String(str ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// Board place for display: 1 + the number of detected engines strictly more biased, with "="
// when another detected engine has the same value. Not-detected engines have no place.
export function boardPlace(dim, engineId) {
  const ranked = dim.board.ranked;
  const me = ranked.find((r) => r.engine === engineId);
  if (!me) return null;
  const above = ranked.filter((r) => r.value > me.value).length;
  const tied = ranked.filter((r) => r.value === me.value).length > 1;
  return `${above + 1}${tied ? "=" : ""}`;
}
