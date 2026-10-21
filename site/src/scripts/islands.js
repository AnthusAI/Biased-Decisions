// The Charts island (web/projection.json, islands.script). A page that draws charts carries its chart payload
// as JSON (#bd-charts, so nothing is fetched) and one Charts mount point; Papyrus loads this bundle on those
// pages only, and the runtime calls Charts once the document is ready.
import { responsive, heroMatrix, boardChart, spider, intervalStrip, legend, versusFloor, forest } from "./charts.js";
import { openFragment } from "./hash.js";

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

window.papyrusIslands = {
  ...window.papyrusIslands,
  Charts() {
    mountCharts();
    openFragment();
  },
};
