// The only script every page runs. The page itself is static HTML built from the data contract;
// this draws its charts (from the JSON payload the page carries, so nothing is fetched), wires the
// theme toggle, and opens a <details> the URL's #fragment points at.
import { responsive, heroMatrix, boardChart, spider, intervalStrip, legend, versusFloor, forest } from "./charts.js";

function currentTheme() {
  const t = document.documentElement.dataset.theme;
  if (t) return t;
  return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function initThemeToggle() {
  const btn = document.querySelector(".theme-toggle");
  if (!btn) return;
  const sync = () => {
    const dark = currentTheme() === "dark";
    btn.setAttribute("aria-pressed", String(dark));
    btn.setAttribute("aria-label", dark ? "Switch to light theme" : "Switch to dark theme");
    btn.textContent = dark ? "Light" : "Dark";
  };
  btn.addEventListener("click", () => {
    const next = currentTheme() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("bd-theme", next); } catch (_) { /* storage blocked */ }
    sync();
  });
  sync();
}

function mountCharts() {
  const node = document.getElementById("bd-charts");
  if (!node) return;
  const payload = JSON.parse(node.textContent);
  const engines = payload.engines;
  const byId = Object.fromEntries(engines.map((e) => [e.id, e]));
  for (const el of document.querySelectorAll("[data-chart]")) {
    const spec = payload.charts[el.dataset.chart];
    if (!spec) continue;
    let draw;
    if (spec.type === "hero") draw = heroMatrix({ engines, dimensions: spec.dims });
    else if (spec.type === "board") draw = boardChart({ engines }, spec.dim);
    else if (spec.type === "versus") draw = versusFloor({ engines }, spec.dim);
    else if (spec.type === "forest") draw = forest({ ...spec, engines: spec.engines ? spec.engines.map((id) => byId[id]) : engines });
    else if (spec.type === "strip") draw = intervalStrip({ ...spec, engine: byId[spec.engine] });
    else if (spec.type === "spider") {
      draw = spider({
        ...spec,
        series: spec.series.map((sr) => ({ ...sr, engine: byId[sr.engine] })),
        hrefFor: (en, a) => (spec.hrefs && spec.hrefs[en.id] && spec.hrefs[en.id][a.id]) || a.href || null,
      });
    }
    if (draw) responsive(el, draw);
  }
  for (const el of document.querySelectorAll("[data-legend]")) {
    const ids = el.dataset.legend.split(",").filter(Boolean);
    el.replaceWith(legend(ids.map((id) => byId[id]), { hollow: el.dataset.hollow !== "false" }));
  }
}

function openFragment() {
  if (!location.hash) return;
  const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
  if (target && target.tagName === "DETAILS") target.open = true;
}

initThemeToggle();
mountCharts();
openFragment();
window.addEventListener("hashchange", openFragment);
window.addEventListener("beforeprint", () => document.querySelectorAll("details").forEach((d) => (d.open = true)));
