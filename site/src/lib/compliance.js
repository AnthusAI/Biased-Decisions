// The compliance layer of the site (BD-7ee753): which pages carry a regulated-decision warning,
// what each risk panel says, and how every piece of evidence is worded and linked. Everything is
// read from data.compliance (bd report --json); the words here only frame numbers the data file
// carries, with the model as the grammatical subject.
import { data, engineById, dimById, urls, cellOf, groupOf, itemOf, fmt, int, facetUnit, isRate, textsOf, taskWord,
  sureBetween, controlOf } from "./site.js";
import { doesAt, positionOf, dimPositionOf } from "./cards.js";

export const C = data.compliance;
const BASE = urls.home();
export const curls = {
  howToFail: (anchor) => `${BASE}how-to-fail/${anchor ? `#${anchor}` : ""}`,
  guidance: (anchor) => `${BASE}guidance/${anchor ? `#${anchor}` : ""}`,
};
export const REPO_BLOB = "https://github.com/AnthusAI/Biased-Decisions/blob/main/";

const byId = (list) => Object.fromEntries(list.map((x) => [x.id, x]));
export const citationById = byId(C.citations);
export const practiceById = byId(C.practices);
export const recipeById = byId(C.recipes);
export const insightById = byId(C.insights);
export const evidenceById = byId(C.evidence);
export const articleById = byId(C.articles);
export const mappingOf = (dimId) => C.mapping.find((m) => m.dimension === dimId);
export const isRegulated = (dimId) => !!(mappingOf(dimId) && mappingOf(dimId).regulated);
export const regulatedDims = C.mapping.filter((m) => m.regulated).map((m) => m.dimension);

// The warning's accessible name: the words a screen reader hears, never colour alone.
export const warnLabel = (dimId) => `Regulated decision: ${practiceById[mappingOf(dimId).practice].label.toLowerCase()}. Read the risk.`;

// ---------------------------------------------------------------------------------------------
// Shortlist rows
// ---------------------------------------------------------------------------------------------
export const shortlistBlock = (task) => C.shortlist.pairs.find((b) => b.task === task) || null;
export const shortlistRowId = (r) => `shortlist-${r.engine}-${r.variant.replace(/_/g, "-")}-${r.cut}`;
export const shortlistHref = (task, r) => `${urls.dim("gender")}${task}/#${shortlistRowId(r)}`;
const shortRow = (ev) => shortlistBlock(ev.task).rows.find((r) => r.engine === ev.engine && r.variant === ev.variant && r.cut === ev.cut);
const plain = (t) => String(t).replace(/\*/g, "").replace(/\s*\(see [^)]*above\)/g, "");
const per100 = (rate) => fmt(rate * 100, 1);
const role = (task) => (task === "paralegal-attorney" ? "attorneys" : "physicians");

// ---------------------------------------------------------------------------------------------
// One piece of evidence, in words and numbers, with the link that proves it.
// Returns { sentence, figure, href, external, example, note }.
// ---------------------------------------------------------------------------------------------
function cellFinding(dimId, group, item, engineId) {
  const dim = dimById[dimId];
  const cell = cellOf(dim, group, item);
  const f = cell.engines[engineId];
  const u = facetUnit(dim, f);
  const href = `${urls.at(dim, group, item)}#${engineId}`;
  const texts = textsOf(dim, item);
  const amount = isRate(u) ? `on ${fmt(f.raw.value)} of every 100 ${texts}` : `by ${fmt(f.raw.value)} percentage points`;
  const ctl = controlOf(f, u);
  const figure = `${amount}. ${ctl.sentence} We are 95% sure the true figure is between ${fmt(f.raw.lo)} and ${fmt(f.raw.hi)}, from ${int(f.n)} ${texts}`;
  const verdict = f.detected ? "a clear effect beyond the control" : "not clearly beyond the control";
  const x = f.extra || {};
  const direction = x.direction_toward_more_female_pct !== undefined && dimId === "gender" && item !== "surgeon-physician"
    ? `When its answer changed, it moved toward “${x.more_female_label.replace(/_/g, " ")}” for the version that read as a woman ${fmt(x.direction_toward_more_female_pct, 1)} times in 100`
    : null;
  return { sentence: doesAt(dim, group, item, engineId), figure, verdict, detected: f.detected,
    what: f.raw.label, href, example: cell.example ? `${urls.at(dim, group, item)}#example` : null, direction };
}

export function describeEvidence(ev) {
  if (ev.kind === "cell") return { id: ev.id, kind: ev.kind, ...cellFinding(ev.dimension, ev.group, ev.item, ev.engine) };
  if (ev.kind === "shortlist") {
    const r = shortRow(ev);
    const en = engineById[ev.engine].label;
    const who = role(ev.task);
    const twin = ev.variant === "twin_averaged";
    const put = `put ${per100(r.women_shortlist_rate)} of every 100 women ${who} on a shortlist of the top ${int(r.cut)} of 2,000 bios, against ${per100(r.men_shortlist_rate)} of every 100 men`;
    const sentence = twin ? `Asked twice about each bio, once as written and once with the pronouns swapped, then averaged, ${en} ${put}` : `${en} ${put}`;
    const figure = `a shortlist ratio of ${fmt(r.four_fifths_ratio)} (the women's rate divided by the men's; 1.00 is equal). We are 95% sure the true figure is between ${fmt(r.ratio_ci[0])} and ${fmt(r.ratio_ci[1])}. Counting applicants the model scored equally as a group, not in file order, gives ${fmt(r.tie_fair_ratio)}. ${en} got the role right for ${fmt(r.accuracy * 100, 1)} of every 100 bios. The test had ${int(r.n_women_positive)} women and ${int(r.n_men_positive)} men who really were ${who}`;
    const counter = twin ? null
      : `${int(r.women_who_gain_place_read_as_men)} of the ${int(r.n_women_positive)} women ${who} made the list only when their bio was read as a man's. ${int(r.men_who_gain_place_read_as_women)} men made it only when read as a woman's`;
    return { id: ev.id, kind: ev.kind, sentence, figure, verdict: r.four_fifths_ratio < C.shortlist.line ? `under ${fmt(C.shortlist.line)}, the level U.S. hiring guidance treats as a warning sign` : `at or above ${fmt(C.shortlist.line)}, the level U.S. hiring guidance treats as a warning sign`,
      detected: r.four_fifths_ratio < C.shortlist.line, ratio: fmt(r.four_fifths_ratio), href: shortlistHref(ev.task, r), direction: counter, example: null };
  }
  if (ev.kind === "prereg") {
    // The row's plain sentence, then what we saw; never the raw measurement string.
    const said = ev.plain ? plain(ev.plain).trim().replace(/[.:;]+$/, "") : "Result";
    return { id: ev.id, kind: ev.kind, sentence: said, figure: plain(ev.observed),
      verdict: plain(ev.verdict), prediction: plain(ev.prediction), href: `${REPO_BLOB}${ev.source}`, external: true,
      article: articleById[ev.article], example: null, direction: null };
  }
  if (ev.kind === "floor") {
    const en = engineById[ev.engine].label;
    return { id: ev.id, kind: ev.kind, sentence: `Asked the same ${taskWord(ev.task, ev.task_label)} question twice about the same unchanged bio, ${en} changes its answer`,
      figure: `on ${fmt(ev.value)} of every 100 bios, out of ${int(ev.n)} tested. That is how much it moves for no reason at all`, verdict: "floor",
      href: `${urls.dim("option-order")}${ev.task}/#${ev.engine}`, example: null, direction: null };
  }
  throw new Error(`unknown evidence kind ${ev.kind}`);
}
export const evidence = (id) => {
  const ev = evidenceById[id];
  if (!ev) throw new Error(`no evidence ${id}`);
  return describeEvidence(ev);
};

// ---------------------------------------------------------------------------------------------
// A risk panel's findings for one page: the page's own measured cells, most biased first.
// ---------------------------------------------------------------------------------------------
// The most biased engine, and beside it the least biased measured one (so a reader sees the range,
// not two copies of the same model); with nothing detected, the engines as measured.
function fromBoard(dim, board, positionFor) {
  const rows = [...board.ranked, ...board.not_detected];
  const pick = rows.length > 1 ? [rows[0], rows[rows.length - 1]] : rows;
  return pick.map((r) => { const [g, i] = positionFor(r.engine); return cellFinding(dim.id, g, i, r.engine); });
}

export function panelFindings(dim, { level = null, engineId = null } = {}) {
  let found;
  if (level) {
    found = fromBoard(dim, level.board, (e) => positionOf(dim, level, level.heads[e]));
  } else if (engineId && dim.cells[engineId].status === "measured") {
    found = [cellFinding(dim.id, ...dimPositionOf(dim, engineId), engineId)];
  } else {
    found = fromBoard(dim, dim.board, (e) => dimPositionOf(dim, e));
  }
  if (!found.length) throw new Error(`risk panel for ${dim.id}: no measured cell to point to`);
  return found;
}

// The shortlist rows a gender page's panel adds: the outcome a screening tool would produce.
export function panelShortlist(dim, { level = null, engineId = null } = {}) {
  if (dim.id !== "gender") return [];
  const task = level ? level.item : "paralegal-attorney";
  if (!shortlistBlock(task)) return [];
  const engs = engineId ? [engineId] : Object.keys(engineById);
  return engs.map((e) => {
    const r = shortlistBlock(task).rows.find((x) => x.engine === e && x.variant === "engine_alone" && x.cut === 500);
    return r ? describeEvidence({ kind: "shortlist", id: null, task, engine: e, variant: "engine_alone", cut: 500 }) : null;
  }).filter(Boolean);
}

export const citationsOf = (dimId) => mappingOf(dimId).citations.map((c) => citationById[c]);
export const recipesOf = (dimId) => mappingOf(dimId).recipes.map((r) => recipeById[r]);
export const insightsOf = (dimId) => mappingOf(dimId).insights.map((i) => insightById[i]);
export const practiceLabel = (id) => (id === "any" ? "Any screening decision above" : practiceById[id].label);
