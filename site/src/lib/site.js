// Everything the pages derive from the data contract (data/leaderboard.json, written by
// `bd report --json`): lookups, the URL scheme, per-page chart payloads, titles, descriptions and
// the plain-language sentences. Pages hold markup only; every rule lives here, once.
import data from "../../data/leaderboard.json";
import { fmt, signed } from "../scripts/util.js";

export { data };
export const engines = data.engines;
export const dimensions = data.dimensions;
export const engineById = Object.fromEntries(engines.map((e) => [e.id, e]));
export const dimById = Object.fromEntries(dimensions.map((d) => [d.id, d]));

export const SITE_NAME = "Biased-Decisions leaderboard";

// ---------------------------------------------------------------------------------------------
// The URL scheme (docs/leaderboard-architecture.md, "URLs"). Every path is lowercase, hyphenated,
// built from ids in the data contract, and ends in a slash.
//
//   /                                   the overall board
//   /<dimension>/                       one dimension's board and its breakdown
//   /<dimension>/<group-or-item>/       one group (a religion, a nationality) or one item (a task,
//                                       a trope question) of that dimension
//   /<dimension>/<group>/<item>/        one cell: a group asked one question (two-axis dimensions)
//   /engines/  /engines/<engine>/  /engines/<engine>/<dimension>/
//   /methods/
// ---------------------------------------------------------------------------------------------
const BASE = import.meta.env.BASE_URL.endsWith("/") ? import.meta.env.BASE_URL : `${import.meta.env.BASE_URL}/`;
const join = (...segs) => BASE + segs.filter(Boolean).map((s) => `${s}/`).join("");

export const urls = {
  home: () => BASE,
  methods: () => join("methods"),
  engines: () => join("engines"),
  engine: (e) => join("engines", e),
  engineDim: (e, d) => join("engines", e, d),
  dim: (d) => join(d),
  // A (group, item) position in a dimension: only axes with more than one value are in the path.
  at: (dim, group, item) => {
    const bd = dim.breakdown;
    return join(dim.id, bd.groups.length > 1 ? group : null, bd.items.length > 1 ? item : null);
  },
  data: () => `${BASE}data/leaderboard.json`,
};

export const absolute = (path, site) => new URL(path, site).href;

// ---------------------------------------------------------------------------------------------
// Breakdown lookups
// ---------------------------------------------------------------------------------------------
export const multiGroup = (dim) => dim.breakdown.groups.length > 1;
export const multiItem = (dim) => dim.breakdown.items.length > 1;
export const groupOf = (dim, id) => dim.breakdown.groups.find((g) => g.id === id);
export const itemOf = (dim, id) => dim.breakdown.items.find((i) => i.id === id);
export const cellOf = (dim, group, item) =>
  dim.breakdown.cells.find((c) => c.group === (group ?? null) && c.item === item);
export const levelOf = (dim, kind, group, item) =>
  dim.breakdown.levels.find((l) => l.kind === kind && l.group === (group ?? null) && l.item === (item ?? null));

// Cells under a level, in axis order: a group's items, an item's groups, a cell itself.
export function cellsUnder(dim, level) {
  const cells = dim.breakdown.cells.filter((c) => Object.values(c.engines).some((f) => f.status === "measured"));
  if (level.kind === "group") return cells.filter((c) => c.group === level.group);
  if (level.kind === "item") return cells.filter((c) => c.item === level.item);
  return cells.filter((c) => c.group === level.group && c.item === level.item);
}

export const groupLabel = (dim, id) => (groupOf(dim, id) || { label: id }).label;
export const itemLabel = (dim, id) => (itemOf(dim, id) || { label: id }).label;
export const cap = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : s);

// What one row of a level is called, and its label.
export function rowKind(dim, level) {
  if (level.kind === "group") return dim.breakdown.item_kind;
  if (level.kind === "item") return multiGroup(dim) ? dim.breakdown.group_kind || "group" : dim.breakdown.item_kind;
  return dim.breakdown.item_kind;
}
export function rowLabel(dim, level, cell) {
  if (level.kind === "group") return itemLabel(dim, cell.item);
  if (level.kind === "item") return multiGroup(dim) ? groupLabel(dim, cell.group) : itemLabel(dim, cell.item);
  return `${groupLabel(dim, cell.group)} · ${itemLabel(dim, cell.item)}`;
}

export function levelTitle(dim, level) {
  if (level.kind === "group") return groupLabel(dim, level.group);
  if (level.kind === "item") return cap(itemLabel(dim, level.item));
  return `${groupLabel(dim, level.group)} · ${itemLabel(dim, level.item)}`;
}
export const levelPath = (dim, level) => urls.at(dim, level.group, level.item);

// Every page below the dimension, for getStaticPaths.
export function levelPages() {
  const out = [];
  for (const dim of dimensions) for (const level of dim.breakdown.levels) out.push({ dim, level });
  return out;
}

// ---------------------------------------------------------------------------------------------
// Pre-registration rows that speak to a position in a dimension.
// ---------------------------------------------------------------------------------------------
function rowsFor(dim, engineId) {
  const c = dim.cells[engineId];
  return c && c.prereg ? c.prereg.map((r) => ({ ...r, engine: engineId })) : [];
}
export function preregAt(dim, { group = null, item = null } = {}) {
  const all = engines.flatMap((e) => rowsFor(dim, e.id)).concat(dim.breakdown.pending || []);
  const facetHit = (r, id) => id && r.facets && r.facets.includes(id);
  return all.filter((r) => {
    if (group && item) return (facetHit(r, item) || facetHit(r, group)) && (!r.groups || r.groups.includes(group));
    if (group) return (r.groups && r.groups.includes(group)) || facetHit(r, group);
    if (item) return facetHit(r, item);
    return true;
  });
}

// ---------------------------------------------------------------------------------------------
// Chart payloads: the slim shapes js/charts.js draws from, with every link precomputed so the
// client never needs the URL scheme.
// ---------------------------------------------------------------------------------------------
const slimFacet = (f) => f.status !== "measured"
  ? { id: f.id, label: f.label, status: f.status }
  : { id: f.id, label: f.label, status: f.status, detected: f.detected, attributable: f.attributable,
      raw: { value: f.raw.value, lo: f.raw.lo, hi: f.raw.hi },
      floor: { value: f.floor.value, lo: f.floor.lo, hi: f.floor.hi },
      excess: f.excess };

const slimSummary = (s) => s.status !== "measured" ? { status: s.status }
  : { status: s.status, detected: s.detected, n: s.n, n_facets: s.n_facets, n_facets_detected: s.n_facets_detected,
      headline: s.headline };

// A dimension, in the shape the board chart reads.
export function boardPayload(dim) {
  const cells = {};
  for (const e of engines) {
    const c = dim.cells[e.id];
    cells[e.id] = { ...slimSummary(c), facets: c.facets.map(slimFacet), href: urls.engineDim(e.id, dim.id) };
  }
  return { id: dim.id, label: dim.label, long: dim.long, measure: dim.measure, facet_kind: dim.facet_kind,
    board: dim.board, cells, href: urls.dim(dim.id) };
}

// A level of a dimension, in the same shape: its facets are the cells under it.
export function levelPayload(dim, level) {
  const cells = {};
  const under = cellsUnder(dim, level);
  for (const e of engines) {
    const facets = under.map((c) => ({ ...slimFacet(c.engines[e.id]), id: facetIdAt(dim, level, c), label: rowLabel(dim, level, c) }));
    cells[e.id] = { ...slimSummary(level.heads[e.id]), facets, href: `${levelPath(dim, level)}#${e.id}` };
  }
  return { id: `${dim.id}/${level.group || ""}/${level.item || ""}`, label: levelTitle(dim, level),
    long: `${dim.long}: ${levelTitle(dim, level)}`, measure: dim.measure, facet_kind: rowKind(dim, level),
    board: level.board, cells, href: levelPath(dim, level) };
}

export function facetIdAt(dim, level, cell) {
  if (level.kind === "group") return cell.item;
  if (level.kind === "item") return multiGroup(dim) ? cell.group : cell.item;
  return cell.item;
}

// The hero: every dimension's headlines.
export function heroPayload() {
  return dimensions.map((d) => {
    const cells = {};
    for (const e of engines) cells[e.id] = { ...slimSummary(d.cells[e.id]), href: urls.engineDim(e.id, d.id) };
    return { id: d.id, label: d.label, long: d.long, measure: d.measure, cells, href: urls.dim(d.id) };
  });
}

// One engine's headline per dimension, for a spider.
export function engineSeries(engineId) {
  const values = {};
  for (const d of dimensions) {
    const c = d.cells[engineId];
    values[d.id] = c.status === "measured"
      ? { status: "measured", value: c.headline.value, lo: c.headline.lo, hi: c.headline.hi, detected: c.detected }
      : { status: "missing" };
  }
  return { engine: engineId, values };
}

export function globalSpiderMax() {
  let m = 0;
  for (const d of dimensions) for (const c of Object.values(d.cells)) if (c.status === "measured") m = Math.max(m, c.headline.value);
  return niceMax(m);
}

export function niceMax(v) {
  if (v <= 0) return 1;
  const pow = Math.pow(10, Math.floor(Math.log10(v)));
  for (const m of [1, 2, 2.5, 5, 10]) if (m * pow >= v) return m * pow;
  return 10 * pow;
}

export const shortLabel = (d) => ({ "gender": "Gender", 
  "age": "Age", "disability": "Disability", "religion": "Religion", "nationality": "Nationality", "race": "Race", "sexuality": "Sexuality", "veteran": "Veteran", "option-order": "Order" }[d.id] || d.label);

// ---------------------------------------------------------------------------------------------
// Words
// ---------------------------------------------------------------------------------------------
export const unit = (dim) => (dim.measure === "flip rate" ? "%" : " pts");
// A facet's own unit: a flip rate is a share of items even on a board that mixes it with shifts.
export const facetUnit = (dim, f) => (f && f.raw && /flip rate/i.test(f.raw.label) ? "%" : f && f.raw && /shift/i.test(f.raw.label) ? " pts" : unit(dim));

export function verdictOf(f) {
  if (!f || f.status !== "measured") return { cls: "miss", text: "not measured" };
  if (!f.attributable) return { cls: "un", text: "unattributed" };
  if (f.detected) return { cls: "det", text: "detected" };
  if (f.extra && f.extra.direction === "reverse") return { cls: "rev", text: "reverse of the trope" };
  return { cls: "nd", text: "not detected" };
}

const axisNoun = { religion: "religions", nationality: "nationalities", "name group": "name groups" };

// One sentence a lay reader can quote, for one engine on one cell.
export function cellSentence(dim, cell, engineId) {
  const f = cell.engines[engineId];
  const en = engineById[engineId].label;
  if (!f || f.status !== "measured") return `${en} was not measured here.`;
  const x = f.extra || {};
  if (dim.facet_kind === "question" || x.trope_consistent_answer != null) {
    const item = itemOf(dim, cell.item);
    const others = `the other ${axisNoun[dim.breakdown.group_kind] || "groups"}`;
    const ans = `"${x.trope_consistent_answer}"`;
    const lead = `When a bio opened with "${x.clause.trim()}" ${en} was`;
    const q = `"${item.question}"`;
    if (f.detected) return `${lead} ${fmt(f.raw.value)} points more likely than for ${others} to answer ${ans} to ${q}, the answer the trope predicts.`;
    if (x.direction === "reverse") return `${lead} ${fmt(Math.abs(f.raw.value))} points less likely than for ${others} to answer ${ans} to ${q}: the opposite of the trope.`;
    return `${lead} within [${fmt(f.raw.lo)}, ${fmt(f.raw.hi)}] points of ${others} on ${q}: no trope detected.`;
  }
  if (x.signed_shift_pts !== undefined && x.floor_clause !== undefined && x.clause) {
    return `With "${x.clause.trim()}" in place of "${x.floor_clause.trim()}", ${en}'s probability of "${x.positive}" moved ${signed(x.signed_shift_pts)} points [${fmt(x.signed_ci[0])}, ${fmt(x.signed_ci[1])}], ${f.detected ? "an interval that excludes zero" : f.attributable ? "an interval that includes zero" : "but every religion moved alike on this task, so it is not attributed to religion"}.`;
  }
  const u = facetUnit(dim, f);
  return `${en} measured ${fmt(f.raw.value)}${u} [${fmt(f.raw.lo)}, ${fmt(f.raw.hi)}] (${f.raw.label}) against a floor of ${fmt(f.floor.value)}${u}: ${signed(f.excess.value)} pp over the floor, ${f.detected ? "bias detected" : f.attributable ? "not detected at this floor" : "unattributed"}.`;
}

// The page's lead number, for titles and descriptions.
export function boardLead(board, dim) {
  const top = board.ranked[0];
  if (top) return `${engineById[top.engine].label} is most biased: ${signed(top.value)} pp over the floor on ${top.facet_label}`;
  if (board.not_detected.length) return `No engine clears the floor (n = ${board.not_detected.map((r) => r.n.toLocaleString("en-US")).join(", ")})`;
  return "No engine measured yet";
}

export function describeDim(dim) {
  return `${dim.long}: engines ranked by measured bias, most biased first. ${boardLead(dim.board, dim)}. Every ${dim.breakdown.groups.length > 1 ? `${dim.breakdown.group_kind} and ` : ""}${dim.breakdown.item_kind}, with intervals, floors and the record behind each number.`;
}

export function describeLevel(dim, level) {
  const t = levelTitle(dim, level);
  const lead = boardLead(level.board, dim);
  if (level.kind === "cell") {
    const cell = cellOf(dim, level.group, level.item);
    const first = level.board.ranked[0] || level.board.not_detected[0];
    return first ? cellSentence(dim, cell, first.engine) : `${dim.long}, ${t}: not measured yet.`;
  }
  const rows = level.kind === "group" ? `question by question` : multiGroup(dim) ? `${dim.breakdown.group_kind} by ${dim.breakdown.group_kind}` : "engine by engine";
  return `${dim.long}, ${t}: ${lead}. Every engine's measurement ${rows}, with its interval and floor.`;
}

export { fmt, signed };

// The facet's own detail lines under its table row: every number the record carries beyond the
// headline measurement.
export function extraLines(dim, f) {
  const x = f.extra || {};
  const out = [];
  if (x.direction_toward_more_female_pct !== undefined) out.push(`${fmt(x.direction_toward_more_female_pct, 1)}% of flips moved toward "${(x.more_female_label || "").replace(/_/g, " ")}" when the bio read as a woman; recall gap ${signed(x.recall_gap_pts)} pts`);
  if (x.direction_share_pct !== undefined) out.push(`${fmt(x.direction_share_pct, 1)}% of ${x.n_flips} flips toward physician for the Black name`);
  if (x.signed_shift_pts !== undefined && x.signed_ci) out.push(`signed shift ${signed(x.signed_shift_pts)} pts [${fmt(x.signed_ci[0])}, ${fmt(x.signed_ci[1])}]${x.flip_vs_floor_pct !== undefined ? `; ${fmt(x.flip_vs_floor_pct)}% of verdicts flipped against the floor` : ""}`);
  if (x.floor_signed_shift_pts !== undefined) out.push(`floor's signed shift ${signed(x.floor_signed_shift_pts, 3)} pts`);
  if (x.all_sample) out.push(`all ${x.all_sample.n.toLocaleString("en-US")} bios: ${signed(x.all_sample.shift_pts, 3)} pts [${fmt(x.all_sample.ci[0], 3)}, ${fmt(x.all_sample.ci[1], 3)}], floor ${signed(x.all_sample.floor_shift_pts, 3)}`);
  if (x.shift_61_minus_34_pts !== undefined) out.push(`shift in P(surgeon), 61 minus 34: ${signed(x.shift_61_minus_34_pts)} pts [${fmt(x.shift_ci[0])}, ${fmt(x.shift_ci[1])}]; 61 vs 62 floor flip ${fmt(x.floor_61_62_flip_pct)}%; ${fmt(x.direction_older_to_surgeon_pct, 1)}% of flips called the older version "surgeon"`);
  if (x.versions) out.push(Object.entries(x.versions).map(([r, v]) => `${cap(r)} ${signed(v.shift_pts)} [${fmt(v.ci[0])}, ${fmt(v.ci[1])}]`).join(" · "));
  if (x.shared_clause_pts !== undefined && x.shared_clause_pts !== null && x.shared_clause_ci) out.push(`shared-clause effect ${signed(x.shared_clause_pts)} pts [${fmt(x.shared_clause_ci[0])}, ${fmt(x.shared_clause_ci[1])}]; spread ${fmt(x.spread_pts)}`);
  if (x.gender_flip_committed_pct !== undefined) out.push(`gender flip rate: committed order ${fmt(x.gender_flip_committed_pct)}%, reversed ${fmt(x.gender_flip_reversed_pct)}%`);
  if (x.max_abs_dp !== undefined) out.push(`largest single-bio change in probability ${fmt(x.max_abs_dp, 3)}`);
  if (x.group_mean_pct !== undefined) out.push(`P(${x.trope_consistent_answer}) with "${x.clause.trim()}" ${fmt(x.group_mean_pct)}%, with the floor "${x.floor_clause.trim()}" ${fmt(x.floor_mean_pct)}%: shift ${signed(x.shift_pts)} pts [${fmt(x.shift_ci[0])}, ${fmt(x.shift_ci[1])}]; ${fmt(x.flip_pct)}% of yes/no verdicts flipped`);
  if (x.general_effect_pts !== undefined && x.general_effect_pts !== null) out.push(`general "any label" effect on this question ${signed(x.general_effect_pts)} pts [${fmt(x.general_effect_ci[0])}, ${fmt(x.general_effect_ci[1])}] (every group alike; cancelled in the trope score)`);
  if (x.question && x.groups) out.push(`"${x.question}" Trope-consistent answer: ${x.trope_consistent_answer}.`);
  if (x.groups) out.push(Object.entries(x.groups).map(([g, v]) => `${cap(g)} ${signed(v.trope_pts)} [${fmt(v.trope_ci[0])}, ${fmt(v.trope_ci[1])}]${v.detected ? "*" : ""}`).join(" · ") + " (trope scores; * interval clears zero)");
  return out;
}

export function filesOf(f) {
  const files = [...(f.records || []), f.study].filter(Boolean);
  if (f.floor && f.floor.record && !files.includes(f.floor.record)) files.push(f.floor.record);
  return files;
}

// Display place on a board: "1", or "1=" when tied.
export function place(board, engineId) {
  const me = board.ranked.find((r) => r.engine === engineId);
  if (!me) return null;
  const above = board.ranked.filter((r) => r.value > me.value).length;
  const tied = board.ranked.filter((r) => r.value === me.value).length > 1;
  return `${above + 1}${tied ? "=" : ""}`;
}

export const int = (n) => (n === null || n === undefined ? "—" : Number(n).toLocaleString("en-US"));

// The page a dimension-level facet id lands on (a task, a question, or a group).
export function facetHref(dim, facetId) {
  if (!multiGroup(dim) && !multiItem(dim)) return urls.dim(dim.id);
  if (dim.facet_kind === "group") return urls.at(dim, facetId, null);
  return urls.at(dim, null, facetId);
}

// One matrix cell: the most biased engine at that cell (or, with nothing detected, how the
// measured engines read), for the dimension page's group x item grid. With `engineId`, that
// engine's own value instead.
export function matrixCell(dim, cell, engineId = null) {
  const href = urls.at(dim, cell.group, cell.item);
  if (engineId) {
    const f = cell.engines[engineId];
    if (f.status !== "measured") return { status: "missing", href };
    return { status: "measured", engine: engineId, value: f.excess.value, lo: f.excess.lo, hi: f.excess.hi,
      detected: f.detected, attributable: f.attributable, reverse: !!(f.extra && f.extra.direction === "reverse"),
      href: `${href}#${engineId}`, prereg: cell.prereg };
  }
  const level = dim.breakdown.levels.find((l) => l.group === cell.group && l.item === cell.item &&
    (l.kind === "cell" || (!multiGroup(dim) && l.kind === "item") || (!multiItem(dim) && l.kind === "group")));
  const board = level ? level.board : null;
  const measured = engines.filter((e) => cell.engines[e.id].status === "measured");
  if (!measured.length) return { status: "missing", href, prereg: cell.prereg };
  const top = board && board.ranked[0];
  if (top) return { status: "measured", engine: top.engine, value: top.value, lo: top.lo, hi: top.hi, detected: true, href, prereg: cell.prereg, n_measured: measured.length };
  const best = measured.map((e) => ({ e, f: cell.engines[e.id] })).sort((a, b) => b.f.excess.value - a.f.excess.value)[0];
  const allReverse = measured.every((e) => cell.engines[e.id].extra && cell.engines[e.id].extra.direction === "reverse");
  return { status: "measured", engine: best.e.id, value: best.f.excess.value, lo: best.f.excess.lo, hi: best.f.excess.hi,
    detected: false, attributable: best.f.attributable, reverse: allReverse, href, prereg: cell.prereg, n_measured: measured.length };
}

// Rows of a forest chart for a level (or a whole dimension's single axis): sorted most biased
// first by the largest excess any engine shows on the row, unmeasured rows last.
export function forestRows(dim, cells, labelOf, hrefOf) {
  const rows = cells.map((c) => {
    const values = {};
    let top = -Infinity;
    for (const e of engines) {
      const f = c.engines[e.id];
      if (f.status !== "measured") { values[e.id] = { status: "missing" }; continue; }
      values[e.id] = { status: "measured", value: f.excess.value, lo: f.excess.lo, hi: f.excess.hi, detected: f.detected,
        attributable: f.attributable, reverse: !!(f.extra && f.extra.direction === "reverse") };
      top = Math.max(top, f.excess.value);
    }
    const href = hrefOf(c);
    return { id: `${c.group || ""}/${c.item}`, label: labelOf(c), tag: c.prereg ? "pre-registered" : null, href,
      hrefs: Object.fromEntries(engines.map((e) => [e.id, `${href}#${e.id}`])), values, _top: top };
  });
  rows.sort((a, b) => b._top - a._top);
  return rows.map(({ _top, ...r }) => r);
}

export const siblingsOf = (list, id) => list.filter((x) => x.id !== id);

export const plural = (k) => ({ nationality: "nationalities", religion: "religions", "name group": "name groups", engine: "engines" }[k] || `${k}s`);

// An engine's largest detected bias over every dimension, in points (0 when none is detected).
export function largestBias(engineId) {
  const found = dimensions.map((d) => d.cells[engineId]).filter((c) => c.status === "measured" && c.detected);
  return found.length ? Math.max(...found.map((c) => c.headline.value)) : 0;
}

// The opioid and comment tasks are not hiring decisions: on a board that mixes them with hiring
// tasks, their own pages carry no hiring warning.
export const NON_HIRING_ITEMS = ["qpain-treatment", "civil-comments-moderation"];
export const isNonHiring = (level) => !!(level && level.item && NON_HIRING_ITEMS.includes(level.item));
