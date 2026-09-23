// The compliance layer of the site (BD-7ee753): which pages carry a regulated-decision warning,
// what each risk panel says, and how every piece of evidence is worded and linked. Everything is
// read from data.compliance (bd report --json); the words here only frame numbers the data file
// carries, with the model as the grammatical subject.
import { data, engineById, dimById, urls, cellOf, groupOf, itemOf, fmt, int, unit } from "./site.js";
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
export const shortlistHref = (task, r) => `${urls.dim("gender-pronouns")}${task}/#${shortlistRowId(r)}`;
const shortRow = (ev) => shortlistBlock(ev.task).rows.find((r) => r.engine === ev.engine && r.variant === ev.variant && r.cut === ev.cut);
const plain = (t) => String(t).replace(/\*/g, "");
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
  const u = unit(dim);
  const href = `${urls.at(dim, group, item)}#${engineId}`;
  const figure = `${fmt(f.raw.value)}${u} [${fmt(f.raw.lo)}, ${fmt(f.raw.hi)}] against a floor of ${fmt(f.floor.value)}${u}, n = ${int(f.n)}`;
  const verdict = f.detected ? "detected" : "no bias detected at this floor";
  const x = f.extra || {};
  const direction = x.direction_toward_more_female_pct !== undefined && dimId === "gender-pronouns" && item !== "surgeon-physician"
    ? `${fmt(x.direction_toward_more_female_pct, 1)}% of its flips moved toward “${x.more_female_label.replace(/_/g, " ")}” when the bio read as a woman`
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
    const sentence = twin
      ? `${en}, scoring each bio and its pronoun-swapped twin and averaging, shortlisted women ${who} at ${per100(r.women_shortlist_rate)} per 100 and men at ${per100(r.men_shortlist_rate)} (top ${int(r.cut)} of 2,000)`
      : `${en} shortlisted women ${who} at ${per100(r.women_shortlist_rate)} per 100 and men at ${per100(r.men_shortlist_rate)} (top ${int(r.cut)} of 2,000)`;
    const figure = `four-fifths ratio ${fmt(r.four_fifths_ratio)} [${fmt(r.ratio_ci[0])}, ${fmt(r.ratio_ci[1])}], tie-fair ${fmt(r.tie_fair_ratio)}; accuracy ${fmt(r.accuracy * 100, 1)}%; n = ${int(r.n_women_positive)} women and ${int(r.n_men_positive)} men`;
    const counter = twin ? null
      : `${int(r.women_who_gain_place_read_as_men)} of ${int(r.n_women_positive)} women ${who} made the list only when read as men; ${int(r.men_who_gain_place_read_as_women)} men made it only when read as women`;
    return { id: ev.id, kind: ev.kind, sentence, figure, verdict: r.four_fifths_ratio < C.shortlist.line ? "under the four-fifths line" : "above the four-fifths line",
      detected: r.four_fifths_ratio < C.shortlist.line, ratio: fmt(r.four_fifths_ratio), href: shortlistHref(ev.task, r), direction: counter, example: null };
  }
  if (ev.kind === "prereg") {
    return { id: ev.id, kind: ev.kind, sentence: `Pre-registered: ${ev.measurement}`, figure: `observed ${plain(ev.observed)}`,
      verdict: plain(ev.verdict), prediction: plain(ev.prediction), href: `${REPO_BLOB}${ev.source}`, external: true,
      article: articleById[ev.article], example: null, direction: null };
  }
  if (ev.kind === "floor") {
    const en = engineById[ev.engine].label;
    return { id: ev.id, kind: ev.kind, sentence: `${en} changes its ${ev.task_label} call when the same bio is asked twice`,
      figure: `${fmt(ev.value)}% of bios, n = ${int(ev.n)} (the ask-twice floor)`, verdict: "floor",
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
  if (dim.id !== "gender-pronouns") return [];
  const task = level ? level.item : "paralegal-attorney";
  if (!shortlistBlock(task)) return [];
  const engs = engineId ? [engineId] : ["laya", "jev"];
  return engs.map((e) => {
    const r = shortlistBlock(task).rows.find((x) => x.engine === e && x.variant === "engine_alone" && x.cut === 500);
    return r ? describeEvidence({ kind: "shortlist", id: null, task, engine: e, variant: "engine_alone", cut: 500 }) : null;
  }).filter(Boolean);
}

export const citationsOf = (dimId) => mappingOf(dimId).citations.map((c) => citationById[c]);
export const recipesOf = (dimId) => mappingOf(dimId).recipes.map((r) => recipeById[r]);
export const insightsOf = (dimId) => mappingOf(dimId).insights.map((i) => insightById[i]);
export const practiceLabel = (id) => (id === "any" ? "Any screening decision above" : practiceById[id].label);
