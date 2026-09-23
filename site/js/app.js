// The Biased-Decisions leaderboard: one data file (data/leaderboard.json, written by
// `bd report --json`), four page types. Every URL is relative, so the site works from a
// sub-path (GitHub Pages) as well as from the root of a local static server.
import { h, fmt, signed, int, qs, rankText, rawUnit, rawText, excessText, niceMax, markerIcon, boardPlace } from "./util.js";
import { responsive, heroMatrix, boardChart, spider, intervalStrip, legend, versusFloor } from "./charts.js";

const DATA_URL = "data/leaderboard.json";

async function main() {
  initTheme();
  const page = document.body.dataset.page;
  const root = document.getElementById("app");
  let data;
  try {
    const res = await fetch(DATA_URL, { cache: "no-cache" });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    data = await res.json();
  } catch (err) {
    root.replaceChildren(h("section", { class: "wrap error" },
      h("h1", { class: "display" }, "The data file did not load"),
      h("p", {}, `Could not read ${DATA_URL} (${err.message}). Serve this folder over HTTP, e.g. `,
        h("code", {}, "python3 -m http.server"), " from site/, rather than opening the file directly.")));
    return;
  }
  injectEngineColours(data.engines);
  document.getElementById("masthead").replaceChildren(masthead(data, page));
  const pages = { overview: renderOverview, dimension: renderDimension, engine: renderEngine, methods: renderMethods };
  root.replaceChildren(...[].concat(pages[page](data)));
  root.append(honestyPanel(data));
  document.getElementById("colophon").replaceChildren(colophon(data));
  root.setAttribute("aria-busy", "false");
  if (location.hash) {
    const target = document.getElementById(location.hash.slice(1));
    if (target) {
      if (target.tagName === "DETAILS") target.open = true;
      requestAnimationFrame(() => target.scrollIntoView({ block: "start" }));
    }
  }
  window.addEventListener("beforeprint", () => document.querySelectorAll("details").forEach((d) => (d.open = true)));
}

// ---------------------------------------------------------------------------------------------
// Chrome
// ---------------------------------------------------------------------------------------------
function initTheme() {
  let saved = null;
  try { saved = localStorage.getItem("bd-theme"); } catch (_) { /* storage blocked */ }
  if (saved === "light" || saved === "dark") document.documentElement.dataset.theme = saved;
}

function currentTheme() {
  const t = document.documentElement.dataset.theme;
  if (t) return t;
  return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function themeButton() {
  const btn = h("button", { type: "button", class: "theme-toggle" });
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
  return btn;
}

function injectEngineColours(engines) {
  const light = engines.map((e) => `--eng-${e.id}: ${e.color};`).join(" ");
  const dark = engines.map((e) => `--eng-${e.id}: ${e.color_dark || e.color};`).join(" ");
  const css = `:root { ${light} }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { ${dark} } }
:root[data-theme="dark"] { ${dark} }
@media print { :root, :root:not([data-theme="light"]), :root[data-theme="dark"] { ${light} } }`;
  document.head.append(h("style", { id: "engine-colours" }, css));
}

function masthead(data, page) {
  const d = qs("d"), e = qs("e");
  const nav = h("nav", { class: "topnav", "aria-label": "Site" },
    h("a", { href: "./", class: page === "overview" ? "on" : null, "aria-current": page === "overview" ? "page" : null }, "Leaderboard"),
    data.engines.map((en) => h("a", { href: `engine.html?e=${en.id}`, class: e === en.id ? "on" : null, "aria-current": e === en.id ? "page" : null }, markerIcon(en, 11), en.label)),
    h("a", { href: "methods.html", class: page === "methods" ? "on" : null, "aria-current": page === "methods" ? "page" : null }, "Methods"),
    themeButton());
  const rail = h("nav", { class: "rail", "aria-label": "Dimensions" },
    h("span", { class: "rail-h" }, "Dimensions"),
    data.dimensions.map((dim) => h("a", { href: `dimension.html?d=${dim.id}`, class: d === dim.id ? "on" : null, "aria-current": d === dim.id ? "page" : null }, dim.label)));
  return h("div", { class: "mast-inner" },
    h("div", { class: "wrap mast-row" },
      h("a", { href: "./", class: "brand" }, h("span", { class: "brand-a" }, "Biased"), h("span", { class: "brand-b" }, "Decisions")),
      nav),
    h("div", { class: "wrap" }, rail));
}

function honestyPanel(data) {
  return h("aside", { class: "wrap honesty", id: "honesty", "aria-labelledby": "honesty-h" },
    h("h2", { id: "honesty-h", class: "display sm" }, "Read this before the board"),
    h("ol", {}, data.honesty.map((x) => h("li", {}, h("strong", {}, x.title), h("span", {}, x.text)))));
}

function colophon(data) {
  const p = data.provenance;
  return h("div", { class: "wrap colo" },
    h("p", {}, "Every number on this site was generated on ", h("strong", {}, p.generated || "an unrecorded date"),
      " from record commit ", h("code", {}, p.record_commit_short || "unknown"), " by ", h("code", {}, p.command), "."),
    h("p", {}, "Sources: ", p.sources.map((src, i) => [i ? "; " : "", h("code", {}, src.path), ` (${src.regenerated_by ? `regenerated by ${src.regenerated_by}` : "staged, not yet regenerable by the harness"})`]), "."),
    h("p", { class: "fine" }, "Biased-Decisions is MIT-licensed. Bias in Bios (De-Arteaga et al., 2019) is MIT-licensed on the Hugging Face Hub. Typography: Jersey 25 and Montserrat (SIL Open Font License), from Google Fonts. No charting library: every chart is hand-drawn SVG."));
}

// ---------------------------------------------------------------------------------------------
// Shared bits
// ---------------------------------------------------------------------------------------------
const engineById = (data) => Object.fromEntries(data.engines.map((e) => [e.id, e]));
const engineName = (en) => h("span", { class: "eng" }, markerIcon(en, 12), en.label);

function mount(chartFn, cls = "chart-box") {
  const box = h("div", { class: cls });
  requestAnimationFrame(() => responsive(box, chartFn));
  return box;
}

function globalSpiderMax(data) {
  let m = 0;
  for (const d of data.dimensions) for (const c of Object.values(d.cells)) if (c.status === "measured") m = Math.max(m, c.headline.value);
  return niceMax(m);
}

function engineSeries(data, en) {
  const values = {};
  for (const d of data.dimensions) {
    const c = d.cells[en.id];
    values[d.id] = c.status === "measured"
      ? { status: "measured", value: c.headline.value, lo: c.headline.lo, hi: c.headline.hi, detected: c.detected }
      : { status: "missing" };
  }
  return { engine: en, values };
}

function largestFinding(data) {
  let best = null;
  for (const d of data.dimensions) for (const en of data.engines) {
    const c = d.cells[en.id];
    if (c.status === "measured" && c.detected && (!best || c.headline.value > best.c.headline.value)) best = { d, en, c };
  }
  return best;
}

// ---------------------------------------------------------------------------------------------
// Overview
// ---------------------------------------------------------------------------------------------
function renderOverview(data) {
  const best = largestFinding(data);
  const nDims = data.dimensions.length;
  const nCells = data.dimensions.reduce((a, d) => a + Object.values(d.cells).filter((c) => c.status === "measured").length, 0);
  const hero = h("section", { class: "wrap hero" },
    h("div", { class: "hero-top" }, h("div", {},
    h("p", { class: "kicker" }, "Bias leaderboard for fast decision models"),
    h("h1", { class: "display xl" }, "Change one detail about a person. Watch the verdict move."),
    h("p", { class: "deck" }, `We edit real professional bios in exactly one protected detail (a pronoun, a name, a stated age, one inserted clause) and measure how far each engine's decision moves beyond what an equally trivial edit moves it. ${data.engines.length} engines, ${nDims} dimensions, ${nCells} measured cells. The most biased engine sits at the top of every board.`)),
    best && h("p", { class: "finding" },
      h("span", { class: "finding-num" }, `${fmt(best.c.headline.raw.value)}${rawUnit(best.d).trim() === "%" ? "%" : " pts"}`),
      h("span", { class: "finding-txt" }, `of ${best.c.headline.facet_label} bios changed verdict for `, engineName(best.en),
        ` when only the ${best.d.label.toLowerCase()} cue changed: `, h("strong", {}, `${signed(best.c.headline.value)} pp over its floor`),
        `, the largest bias measured anywhere on this board.`))),
    h("figure", { class: "hero-fig" },
      h("figcaption", {},
        h("span", { class: "fig-t" }, "Every measured bias, on one scale"),
        h("span", { class: "fig-d" }, "Each mark is an engine's largest excess over the floor in that dimension, with its 95% interval. Marks start at the floor and travel to the measurement. Select any mark for the task-level table.")),
      legend(data.engines),
      mount(heroMatrix(data), "chart-box hero-box")));

  // Overall board
  const rows = data.overall.rows;
  const byEngine = engineById(data);
  let place = 0, lastMean = null;
  const board = h("ol", { class: "overall" }, rows.map((r, i) => {
    if (r.mean_rank !== lastMean) place = i + 1;
    lastMean = r.mean_rank;
    const en = byEngine[r.engine];
    return h("li", { class: "ov-row" },
      h("div", { class: "ov-place", "aria-label": `Place ${place}` }, String(place)),
      h("div", { class: "ov-name" },
        h("a", { href: `engine.html?e=${en.id}` }, engineName(en)),
        h("div", { class: "ov-mean" }, h("strong", {}, fmt(r.mean_rank)), ` mean rank across ${r.ranked_on} contested dimension${r.ranked_on === 1 ? "" : "s"}`),
        r.incomplete && h("div", { class: "flag" }, `Incomplete: not measured on ${r.unmeasured.length} of ${data.overall.n_dimensions}`)),
      coverageStrip(data, r));
  }));
  const overall = h("section", { class: "wrap section" },
    h("h2", { class: "display" }, "The overall board"),
    h("p", { class: "lede" }, "Engines ordered by their mean rank across the dimensions where they could be compared with another engine; rank 1 means most biased. Nothing is averaged in for a dimension an engine was never measured on."),
    board,
    h("div", { class: "cov-key", "aria-hidden": "true" },
      h("span", {}, h("i", { class: "cv r1" }, "1"), "rank on that board"),
      h("span", {}, h("i", { class: "cv nd" }, "1.5"), "no bias detected: shares the bottom places"),
      h("span", {}, h("i", { class: "cv sole" }, "only"), "only engine measured: not ranked"),
      h("span", {}, h("i", { class: "cv miss" }, ""), "not measured")),
    h("p", { class: "note" }, data.overall.rule));

  // Spiders
  const max = globalSpiderMax(data);
  const axes = data.dimensions.map((d) => ({ id: d.id, label: d.label, short: shortLabel(d), href: `dimension.html?d=${d.id}` }));
  const spiders = h("section", { class: "wrap section" },
    h("h2", { class: "display" }, "The shape of each engine's bias"),
    h("p", { class: "lede" }, "One axis per dimension, radius equal to the excess over the floor, on the same scale for every engine. This is the inverse of a capability chart: ", h("strong", {}, "a bigger shape is a worse model."), " A dashed axis was never measured, and the shape is broken there rather than pulled to zero."),
    h("div", { class: "spider-row" }, data.engines.map((en) => h("a", { class: "spider-card", href: `engine.html?e=${en.id}` },
      h("div", { class: "spider-h" }, engineName(en)),
      mount(spider({ axes, series: [engineSeries(data, en)], max, compact: true, label: `${en.label}: excess over the floor on every dimension` }), "chart-box spider-box"),
      h("div", { class: "spider-f" }, `${data.dimensions.filter((d) => d.cells[en.id].status === "measured").length} of ${data.dimensions.length} dimensions measured`)))));

  // Dimension index
  const idx = h("section", { class: "wrap section" },
    h("h2", { class: "display" }, "Every dimension"),
    h("div", { class: "dim-grid" }, data.dimensions.map((d) => {
      const top = d.board.ranked[0];
      return h("a", { class: "dim-card", href: `dimension.html?d=${d.id}` },
        h("div", { class: "dim-card-h" }, d.long),
        h("div", { class: "dim-card-top" }, top ? [engineName(byEngine[top.engine]), h("span", {}, ` ${signed(top.value)} pp`)] : h("span", { class: "muted" }, "no engine clears its floor")),
        h("p", {}, d.cue),
        h("div", { class: "dim-card-f" }, d.source === "batch2-staging" ? "staged batch-2 data" : `${d.facets.length} ${d.facet_kind}${d.facets.length === 1 ? "" : "s"}`));
    })));
  return [hero, overall, spiders, idx];
}

function shortLabel(d) {
  const map = { "gender-pronouns": "Gender", "race-name": "Race (first)", "race-fullname": "Race (full)", "age-inserted": "Age", "disability": "Disability", "religion": "Religion v1", "religion-v2": "Religion v2", "stereotype-religion": "Relig. tropes", "stereotype-nationality": "Nat. tropes", "option-order": "Order" };
  return map[d.id] || d.label;
}

function coverageStrip(data, row) {
  const cells = data.dimensions.map((d) => {
    let cls, txt, desc;
    if (row.unmeasured.includes(d.id)) { cls = "miss"; txt = ""; desc = "not measured"; }
    else if (row.sole_engine.includes(d.id)) { cls = "sole"; txt = "only"; desc = "only engine measured, not ranked"; }
    else {
      const pos = row.positions[d.id];
      const nd = row.not_detected.includes(d.id);
      cls = nd ? "nd" : pos <= 1.5 ? "r1" : "r2";
      txt = rankText(pos);
      desc = nd ? `no bias detected, rank ${txt}` : `rank ${txt}`;
    }
    const a = h("a", { href: `dimension.html?d=${d.id}#cell-${row.engine}`, class: `cv ${cls}`, "aria-label": `${d.label}: ${desc}` },
      h("span", { class: "cv-d" }, shortLabel(d)), h("span", { class: "cv-v" }, txt));
    return a;
  });
  return h("div", { class: "cov" }, cells);
}

// ---------------------------------------------------------------------------------------------
// Dimension page
// ---------------------------------------------------------------------------------------------
function renderDimension(data) {
  const dim = data.dimensions.find((d) => d.id === qs("d")) || data.dimensions[0];
  document.title = `${dim.long} · Biased-Decisions leaderboard`;
  const byEngine = engineById(data);
  const openCell = (engineId) => {
    const det = document.getElementById(`cell-${engineId}`);
    if (!det) return;
    det.open = true;
    history.replaceState(null, "", `#cell-${engineId}`);
    det.scrollIntoView({ behavior: "smooth", block: "start" });
    det.querySelector("summary").focus({ preventScroll: true });
  };

  const head = h("section", { class: "wrap hero dim-hero" },
    h("p", { class: "kicker" }, dim.source === "batch2-staging" ? "Dimension · staged batch-2 data" : "Dimension"),
    h("h1", { class: "display xl" }, dim.long),
    h("dl", { class: "defs" },
      h("div", {}, h("dt", {}, "The cue"), h("dd", {}, dim.cue)),
      h("div", {}, h("dt", {}, "The floor"), h("dd", {}, dim.floor)),
      h("div", {}, h("dt", {}, "Ranked on"), h("dd", {}, `Excess: ${dim.excess}.`))),
    dim.notes.length ? h("div", { class: "footnote", role: "note" }, dim.notes.map((n) => h("p", {}, n))) : null);

  const ranked = dim.board.ranked;
  const boardSec = h("section", { class: "wrap section" },
    h("h2", { class: "display" }, "The board"),
    ranked.length
      ? [h("p", { class: "lede" }, `Most biased first. Each bar runs from the engine's floor (grey) to its measurement, so its length is the excess; the whisker is the 95% interval and the thin ticks are the engine's other ${dim.facet_kind}s. Select a row for its ${dim.facet_kind} table.`),
         mount(boardChart(data, dim, openCell))]
      : h("p", { class: "lede strong" }, "No engine's interval clears the floor on this dimension, so nothing is ranked."),
    dim.board.not_detected.length ? h("div", { class: "nd-list" },
      h("h3", {}, "No bias detected at this floor"),
      h("ul", {}, dim.board.not_detected.map((r) => {
        const c = dim.cells[r.engine];
        return h("li", {}, h("a", { href: `#cell-${r.engine}`, onclick: (ev) => { ev.preventDefault(); openCell(r.engine); } }, engineName(byEngine[r.engine])),
          h("span", { class: "nd-n" }, `n = ${int(r.n)} bios${r.n_facets > 1 ? ` (largest of ${r.n_facets} ${dim.facet_kind}s)` : ""}`),
          h("span", { class: "nd-v" }, `measured ${rawText(dim, c.headline.raw)} against a floor of ${fmt(c.headline.floor_value)}${rawUnit(dim)}; excess ${excessText(r)}`));
      })),
      h("p", { class: "note" }, "Absence of evidence at this sample size, not a clean bill of health.")) : null,
    dim.board.unmeasured.length ? h("p", { class: "unmeasured" }, h("span", { class: "hatch" }), h("span", {}, "Not measured on this dimension: ",
      dim.board.unmeasured.map((id, i) => [i ? ", " : "", h("a", { href: `engine.html?e=${id}` }, byEngine[id].label)]), ". Shown as missing, never as zero.")) : null);

  const sections = [head, boardSec];
  const facets = dim.facets;
  if (facets.length < 3) {
    sections.push(h("section", { class: "wrap section" },
      h("h2", { class: "display" }, "Measurement against floor"),
      h("p", { class: "lede" }, "Each engine's measurement (coloured, with its 95% interval) above the floor it is read against (grey band: the floor's own interval). An engine is detected only when its interval clears the floor's point estimate."),
      mount(versusFloor(data, dim))));
  }
  if (facets.length >= 3) {
    const series = data.engines.filter((en) => dim.cells[en.id].status === "measured").map((en) => {
      const values = {};
      for (const f of dim.cells[en.id].facets) {
        values[f.id] = f.status === "measured" ? { status: "measured", value: f.excess.value, lo: f.excess.lo, hi: f.excess.hi, detected: f.detected, attributable: f.attributable } : { status: "missing" };
      }
      return { engine: en, values };
    });
    let m = 0;
    for (const sr of series) for (const v of Object.values(sr.values)) if (v.status === "measured") m = Math.max(m, v.value);
    sections.push(h("section", { class: "wrap section" },
      h("h2", { class: "display" }, `Every ${dim.facet_kind}`),
      h("p", { class: "lede" }, `One axis per ${dim.facet_kind}; radius is the excess over that ${dim.facet_kind}'s floor, so outward is worse. Hollow vertices: no bias detected. A polygon is broken where the engine was not measured.`),
      legend(series.map((sr) => sr.engine)),
      mount(spider({ axes: facets.map((f) => ({ id: f.id, label: f.label })), series, max: niceMax(m || 1),
        label: `${dim.long}: excess over the floor per ${dim.facet_kind} and engine`,
        hrefFor: (en) => `#cell-${en.id}` }), "chart-box spider-big")));
  }

  sections.push(h("section", { class: "wrap section", id: "cells" },
    h("h2", { class: "display" }, `The ${dim.facet_kind} tables`),
    h("p", { class: "lede" }, "One table per engine: every number with its interval, the floor it is read against, the committed files it replays from, and the pre-registered prediction beside what happened."),
    data.engines.map((en) => cellDetails(data, dim, en))));
  // make ticks/vertices open the cell too
  requestAnimationFrame(() => document.querySelectorAll('a.vertex[href^="#cell-"]').forEach((a) =>
    a.addEventListener("click", (ev) => { ev.preventDefault(); openCell(a.getAttribute("href").slice(6)); })));
  return sections;
}

function verdictChip(f) {
  if (f.status !== "measured") return h("span", { class: "chip miss" }, "not measured");
  if (!f.attributable) return h("span", { class: "chip un" }, "unattributed");
  return f.detected ? h("span", { class: "chip det" }, "detected") : h("span", { class: "chip nd" }, "not detected");
}

function extraLines(dim, f) {
  const x = f.extra || {};
  const out = [];
  if (x.direction_toward_more_female_pct !== undefined) out.push(`${fmt(x.direction_toward_more_female_pct, 1)}% of flips moved toward "${(x.more_female_label || "").replace(/_/g, " ")}" when the bio read as a woman; recall gap ${signed(x.recall_gap_pts)} pts`);
  if (x.direction_share_pct !== undefined) out.push(`${fmt(x.direction_share_pct, 1)}% of ${x.n_flips} flips toward physician for the Black name`);
  if (x.signed_shift_pts !== undefined && x.signed_ci) out.push(`signed shift ${signed(x.signed_shift_pts)} pts [${fmt(x.signed_ci[0])}, ${fmt(x.signed_ci[1])}]${x.flip_vs_floor_pct !== undefined ? `; ${fmt(x.flip_vs_floor_pct)}% of verdicts flipped against the floor` : ""}`);
  if (x.floor_signed_shift_pts !== undefined) out.push(`floor's signed shift ${signed(x.floor_signed_shift_pts, 3)} pts`);
  if (x.all_sample) out.push(`all ${int(x.all_sample.n)} bios: ${signed(x.all_sample.shift_pts, 3)} pts [${fmt(x.all_sample.ci[0], 3)}, ${fmt(x.all_sample.ci[1], 3)}], floor ${signed(x.all_sample.floor_shift_pts, 3)}`);
  if (x.shift_61_minus_34_pts !== undefined) out.push(`shift in P(surgeon), 61 minus 34: ${signed(x.shift_61_minus_34_pts)} pts [${fmt(x.shift_ci[0])}, ${fmt(x.shift_ci[1])}]; 61 vs 62 floor flip ${fmt(x.floor_61_62_flip_pct)}%; ${fmt(x.direction_older_to_surgeon_pct, 1)}% of flips called the older version "surgeon"`);
  if (x.versions) out.push(Object.entries(x.versions).map(([r, v]) => `${r} ${signed(v.shift_pts)} [${fmt(v.ci[0])}, ${fmt(v.ci[1])}]`).join(" · "));
  if (x.shared_clause_pts !== undefined && x.shared_clause_pts !== null) out.push(`shared-clause effect ${signed(x.shared_clause_pts)} pts [${fmt(x.shared_clause_ci[0])}, ${fmt(x.shared_clause_ci[1])}]; spread ${fmt(x.spread_pts)}`);
  if (x.gender_flip_committed_pct !== undefined) out.push(`gender flip rate: committed order ${fmt(x.gender_flip_committed_pct)}%, reversed ${fmt(x.gender_flip_reversed_pct)}%`);
  if (x.max_abs_dp !== undefined) out.push(`largest single-bio change in probability ${fmt(x.max_abs_dp, 3)}`);
  if (x.question) out.push(`"${x.question}" Trope-consistent answer: ${x.trope_consistent_answer}. General "any label" effect ${signed(x.general_effect_pts)} pts.`);
  if (x.groups) out.push(Object.entries(x.groups).map(([g, v]) => `${g} ${signed(v.trope_pts)} [${fmt(v.trope_ci[0])}, ${fmt(v.trope_ci[1])}]${v.detected ? "*" : ""}`).join(" · ") + " (trope scores; * interval excludes zero)");
  return out;
}

function fileLinks(f) {
  const files = [...(f.records || []), f.study].filter(Boolean);
  if (f.floor && f.floor.record && !files.includes(f.floor.record)) files.push(f.floor.record);
  return h("ul", { class: "files" }, files.map((p) => h("li", {}, h("code", {}, p))));
}

function cellDetails(data, dim, en) {
  const c = dim.cells[en.id];
  const measured = c.status === "measured";
  const summary = h("summary", {},
    engineName(en),
    measured
      ? h("span", { class: "sum-v" }, c.detected ? `${signed(c.headline.value)} pp over the floor, ${c.headline.facet_label}` : "no bias detected at this floor",
        h("span", { class: "sum-n" }, ` · ${c.n_facets} ${dim.facet_kind}${c.n_facets === 1 ? "" : "s"} measured`))
      : h("span", { class: "sum-v muted" }, "not measured on this dimension"));
  const det = h("details", { id: `cell-${en.id}`, class: "cell" + (measured ? "" : " missing") }, summary);
  if (!measured) {
    det.append(h("p", { class: "note" }, `${en.label} has no record for this dimension. It is shown as missing, never as zero, and it is flagged incomplete on the overall board.`));
    return det;
  }
  const unit = rawUnit(dim);
  const table = h("table", { class: "cell-table" },
    h("caption", { class: "sr" }, `${en.label}, ${dim.long}: per-${dim.facet_kind} measurements`),
    h("thead", {}, h("tr", {},
      h("th", { scope: "col" }, dim.facet_kind), h("th", { scope: "col" }, "measured [95% CI]"), h("th", { scope: "col" }, "floor"),
      h("th", { scope: "col" }, "excess [95% CI]"), h("th", { scope: "col" }, "verdict"), h("th", { scope: "col" }, "n"))),
    h("tbody", {}, c.facets.map((f) => {
      if (f.status !== "measured") {
        return h("tr", { class: "row-miss" }, h("th", { scope: "row" }, f.label), h("td", { colspan: 3, class: "muted" }, `not measured (${f.why})`), h("td", {}, verdictChip(f)), h("td", {}, "—"));
      }
      const lines = extraLines(dim, f);
      return [
        h("tr", { class: f.id === c.headline.facet ? "row-head" : null },
          h("th", { scope: "row" }, f.label, f.id === c.headline.facet ? h("span", { class: "hl" }, c.detected ? "largest" : "largest excess") : null),
          h("td", { class: "num" }, `${fmt(f.raw.value)}${unit}`, h("span", { class: "ci-t" }, ` [${fmt(f.raw.lo)}, ${fmt(f.raw.hi)}]`), h("div", { class: "sub" }, f.raw.label)),
          h("td", { class: "num" }, `${fmt(f.floor.value)}${unit}`, f.floor.lo !== null ? h("span", { class: "ci-t" }, ` [${fmt(f.floor.lo)}, ${fmt(f.floor.hi)}]`) : null, h("div", { class: "sub" }, f.floor.label)),
          h("td", { class: "num strong" }, `${signed(f.excess.value)} pp`, h("span", { class: "ci-t" }, ` [${fmt(f.excess.lo)}, ${fmt(f.excess.hi)}]`)),
          h("td", {}, verdictChip(f)),
          h("td", { class: "num" }, int(f.n))),
        h("tr", { class: "row-more" }, h("td", { colspan: 6 },
          lines.length ? h("ul", { class: "more" }, lines.map((l) => h("li", {}, l))) : null,
          f.note ? h("p", { class: "fnote" }, f.note) : null,
          h("div", { class: "more-meta" }, h("span", {}, `Interval: ${f.interval_method}.`), fileLinks(f)))),
      ];
    })));
  det.append(h("div", { class: "table-scroll", tabindex: "0", role: "region", "aria-label": `${en.label} ${dim.facet_kind} table` }, table));
  if (c.prereg && c.prereg.length) {
    det.append(h("div", { class: "prereg" },
      h("h4", {}, "Pre-registered, then measured"),
      h("p", { class: "note" }, `Quoted verbatim from ${c.prereg[0].source}, section "${c.prereg[0].section}".`),
      c.prereg.map((p) => h("div", { class: "pr" },
        p.measurement ? h("div", { class: "pr-m" }, p.measurement, p.facets ? h("span", { class: "pr-f" }, ` (${p.facets.map((id) => (dim.facets.find((x) => x.id === id) || { label: id }).label).join(", ")})`) : null) : (p.facets ? h("div", { class: "pr-m" }, p.facets.map((id) => (dim.facets.find((x) => x.id === id) || { label: id }).label).join(", ")) : null),
        h("div", { class: "pr-grid" },
          h("div", {}, h("span", { class: "pr-k" }, "Predicted"), h("p", {}, p.prediction)),
          h("div", {}, h("span", { class: "pr-k" }, "Observed"), h("p", {}, p.observed))),
        h("div", { class: "pr-v" }, h("span", { class: "pr-k" }, "Verdict"), " ", p.verdict),
        p.note ? h("p", { class: "fnote" }, p.note) : null))));
  } else {
    det.append(h("p", { class: "note" }, "No pre-registered prediction covers this cell."));
  }
  return det;
}

// ---------------------------------------------------------------------------------------------
// Engine page
// ---------------------------------------------------------------------------------------------
function renderEngine(data) {
  const en = data.engines.find((e) => e.id === qs("e")) || data.engines[0];
  document.title = `${en.label} · Biased-Decisions leaderboard`;
  const row = data.overall.rows.find((r) => r.engine === en.id);
  const measuredDims = data.dimensions.filter((d) => d.cells[en.id].status === "measured");
  const missingDims = data.dimensions.filter((d) => d.cells[en.id].status !== "measured");
  const max = globalSpiderMax(data);
  const axes = data.dimensions.map((d) => ({ id: d.id, label: d.label, href: `dimension.html?d=${d.id}` }));
  const head = h("section", { class: "wrap hero eng-hero" },
    h("p", { class: "kicker" }, `Engine · ${en.kind}`),
    h("h1", { class: "display xl eng-title" }, h("span", { class: "eng-dot", style: `background:var(--eng-${en.id})` }), en.label),
    h("p", { class: "deck" }, en.about),
    h("div", { class: "eng-stats" },
      h("div", {}, h("span", { class: "stat-k" }, "Mean rank"), h("span", { class: "stat-v" }, row.mean_rank === null ? "—" : fmt(row.mean_rank)), h("span", { class: "stat-s" }, `across ${row.ranked_on} contested dimensions; 1 = most biased`)),
      h("div", {}, h("span", { class: "stat-k" }, "Measured on"), h("span", { class: "stat-v" }, `${row.measured_on} / ${data.dimensions.length}`), h("span", { class: "stat-s" }, row.incomplete ? "incomplete: see below" : "complete")),
      h("div", {}, h("span", { class: "stat-k" }, "Bias detected in"), h("span", { class: "stat-v" }, String(measuredDims.filter((d) => d.cells[en.id].detected).length)), h("span", { class: "stat-s" }, "of the dimensions it was measured on"))));
  const spiderSec = h("section", { class: "wrap section" },
    h("h2", { class: "display" }, "Its polygon"),
    h("p", { class: "lede" }, "Radius is the excess over the floor in each dimension, on the same scale as every other engine's page. Bigger is worse. Dashed axes were never measured; the shape breaks there instead of pretending zero."),
    mount(spider({ axes, series: [engineSeries(data, en)], max, label: `${en.label}: excess over the floor on every dimension`, hrefFor: (_, a) => `dimension.html?d=${a.id}#cell-${en.id}` }), "chart-box spider-big"));
  let stripMax = 0;
  for (const d of measuredDims) stripMax = Math.max(stripMax, d.cells[en.id].headline.hi);
  stripMax = niceMax(stripMax);
  const cellsSec = h("section", { class: "wrap section" },
    h("h2", { class: "display" }, "All its cells"),
    h("p", { class: "lede" }, `Largest excess over the floor per dimension, with its 95% interval, on one scale (0 to ${stripMax} pp; the vertical line is the floor).`),
    h("ol", { class: "eng-cells" }, measuredDims.map((d) => {
      const c = d.cells[en.id];
      const pos = row.positions[d.id];
      const status = !d.board.contested ? (c.detected ? "only engine measured" : "only engine measured; no bias detected") : c.detected ? `place ${boardPlace(d, en.id)} of ${Object.values(d.cells).filter((x) => x.status === "measured").length} (mean-rank position ${rankText(pos)})` : `no bias detected (mean-rank position ${rankText(pos)})`;
      return h("li", {},
        h("a", { href: `dimension.html?d=${d.id}#cell-${en.id}`, class: "ec-name" }, d.label),
        h("span", { class: "ec-status" + (c.detected ? "" : " nd") }, status),
        mount(intervalStrip({ ...c.headline, detected: c.detected, engine: en, max: stripMax, min: Math.min(0, Math.floor(c.headline.lo)) >= 0 ? 0 : Math.min(0, c.headline.lo) }), "chart-box strip-box"),
        h("span", { class: "ec-v" }, `${signed(c.headline.value)} pp`, h("span", { class: "ci-t" }, ` [${fmt(c.headline.lo)}, ${fmt(c.headline.hi)}]`), h("span", { class: "ec-f" }, c.headline.facet_label)));
    })));
  const missSec = h("section", { class: "wrap section" },
    h("h2", { class: "display" }, "Where it is unmeasured"),
    missingDims.length
      ? [h("p", { class: "lede" }, `${en.label} has no record on ${missingDims.length} of ${data.dimensions.length} dimensions. None of them counts toward its mean rank, and none of them is zero.`),
         h("ul", { class: "miss-list" }, missingDims.map((d) => h("li", {}, h("span", { class: "hatch" }), h("a", { href: `dimension.html?d=${d.id}` }, d.long))))]
      : h("p", { class: "lede" }, "Measured on every dimension."));
  return [head, spiderSec, cellsSec, missSec];
}

// ---------------------------------------------------------------------------------------------
// Methods page, generated from the data file's vocabulary and dimension definitions.
// ---------------------------------------------------------------------------------------------
function renderMethods(data) {
  const byEngine = engineById(data);
  const p = data.provenance;
  return [
    h("section", { class: "wrap hero" },
      h("p", { class: "kicker" }, "Methods"),
      h("h1", { class: "display xl" }, "How every number here is made"),
      h("p", { class: "deck" }, "Causal counterfactuals on real text: the same bio, one protected detail changed, measured against an equally trivial edit that changes nothing protected. This page is generated from the same data file as the boards.")),
    h("section", { class: "wrap section" },
      h("h2", { class: "display" }, "Vocabulary"),
      h("dl", { class: "vocab" }, data.vocabulary.map((v) => h("div", {}, h("dt", {}, v.term), h("dd", {}, v.text))))),
    h("section", { class: "wrap section" },
      h("h2", { class: "display" }, "Ranking rules"),
      h("ol", { class: "rules" },
        h("li", {}, h("strong", {}, "Detection. "), "A measurement is detected when its 95% interval excludes the floor. The excess interval shown is the measurement's own interval less the floor's point estimate; an interval that touches the floor counts as including it."),
        h("li", {}, h("strong", {}, "A dimension's headline. "), "Where a dimension has several tasks, groups or questions, an engine is placed by its largest excess among the ones where bias was detected: the board shows where the harm is largest. Every other one stays in the table."),
        h("li", {}, h("strong", {}, "The board. "), "Detected engines rank by that excess, most biased first. Engines whose headline interval includes the floor are listed below the board as “no bias detected at this floor” with their sample size."),
        h("li", {}, h("strong", {}, "The overall board. "), data.overall.rule))),
    h("section", { class: "wrap section" },
      h("h2", { class: "display" }, "The dimensions"),
      data.dimensions.map((d) => h("article", { class: "method-dim", id: `m-${d.id}` },
        h("h3", {}, h("a", { href: `dimension.html?d=${d.id}` }, d.long)),
        h("dl", { class: "defs compact" },
          h("div", {}, h("dt", {}, "Cue"), h("dd", {}, d.cue)),
          h("div", {}, h("dt", {}, "Floor"), h("dd", {}, d.floor)),
          h("div", {}, h("dt", {}, "Excess"), h("dd", {}, d.excess)),
          h("div", {}, h("dt", {}, "Measured on"), h("dd", {}, data.engines.filter((e) => d.cells[e.id].status === "measured").map((e) => e.label).join(", ") || "no engine")),
          d.prereg_section ? h("div", {}, h("dt", {}, "Pre-registration"), h("dd", {}, d.prereg_section)) : null,
          h("div", {}, h("dt", {}, "Source"), h("dd", {}, d.source === "batch2-staging" ? "batch-2 staging file (not yet regenerable by bd replay)" : "the harness: studies/*.jsonl, replayed by bd replay"))),
        d.notes.map((n) => h("p", { class: "fnote" }, n))))),
    h("section", { class: "wrap section" },
      h("h2", { class: "display" }, "The ask-twice floor"),
      h("p", { class: "lede" }, "The same bio asked a second time, unchanged: the noise every flip rate on the gender and option-order boards is read against. It is a floor, not a dimension, so it is never ranked."),
      h("div", { class: "table-scroll", tabindex: "0", role: "region", "aria-label": "Ask-twice floors" },
        h("table", { class: "cell-table" },
          h("thead", {}, h("tr", {}, ["engine", "task", "flip rate", "mean |ΔP|", "max |ΔP|", "n", "record"].map((t) => h("th", { scope: "col" }, t)))),
          h("tbody", {}, data.floors.ask_twice.map((f) => h("tr", {},
            h("th", { scope: "row" }, engineName(byEngine[f.engine])), h("td", {}, f.task_label), h("td", { class: "num" }, `${fmt(f.flip_pct)}%`),
            h("td", { class: "num" }, fmt(f.mean_abs_dp, 4)), h("td", { class: "num" }, fmt(f.max_abs_dp, 4)), h("td", { class: "num" }, int(f.n)), h("td", {}, h("code", {}, f.record)))))))),
    h("section", { class: "wrap section" },
      h("h2", { class: "display" }, "Replay it"),
      h("p", { class: "lede" }, "Nothing on this site is live. From a clone of the repository:"),
      h("pre", { class: "code" }, h("code", {}, `make install\n.venv/bin/bd replay                       # re-score every cell from answers/\n.venv/bin/bd report --json --date ${p.generated || "YYYY-MM-DD"}   # write site/data/leaderboard.json\ncd site && python3 -m http.server 8000`)),
      h("p", {}, `This build: record commit `, h("code", {}, p.record_commit || "unknown"), `, generated ${p.generated || "(no date)"}.`),
      h("ul", { class: "sources" }, p.sources.map((src) => h("li", {}, h("code", {}, src.path), ` — ${src.about}`)))),
  ];
}

main();
