// The only script every page runs. The page itself is static HTML built from the data contract;
// this draws its charts (from the JSON payload the page carries, so nothing is fetched) and opens
// a <details> the URL's #fragment points at.
import { responsive, heroMatrix, boardChart, spider, intervalStrip, legend, versusFloor, forest } from "./charts.js";

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
  // The first build's #cell-<engine> fragments (kept by the legacy redirects) name #<engine> now.
  if (/^#cell-[a-z0-9-]+$/.test(location.hash)) {
    history.replaceState(null, "", location.pathname + location.search + location.hash.replace("#cell-", "#"));
    const el = document.getElementById(location.hash.slice(1));
    if (el) el.scrollIntoView();
  }
  const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
  if (target && target.tagName === "DETAILS") target.open = true;
}

mountCharts();
openFragment();
window.addEventListener("hashchange", openFragment);
window.addEventListener("beforeprint", () => document.querySelectorAll("details").forEach((d) => (d.open = true)));
