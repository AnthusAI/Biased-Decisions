// Everything the pages derive from the data contract (data/leaderboard.json, written by
// `bd report --json`): lookups, the URL scheme, per-page chart payloads, titles, descriptions and
// the plain-language sentences. Pages hold markup only; every rule lives here, once.
import data from "../../data/leaderboard.json";
import { fmt, signed } from "../scripts/util.js";

export { data };
export const engines = data.engines;
export const allDimensions = data.dimensions;
// The characteristics (kinds of person). Option order is a supplemental test: it has its own page
// but is not a characteristic and is not ranked.
export const dimensions = allDimensions.filter((d) => !d.supplemental);
export const supplementalDimensions = allDimensions.filter((d) => d.supplemental);
export const engineById = Object.fromEntries(engines.map((e) => [e.id, e]));
export const dimById = Object.fromEntries(allDimensions.map((d) => [d.id, d]));

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
  for (const dim of allDimensions) for (const level of dim.breakdown.levels) out.push({ dim, level });
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

// What a dimension measures, in the words a reader sees (the plain phrase when the data has one).
export const measureOf = (dim) => dim.measure_plain || dim.measure;

// A dimension, in the shape the board chart reads.
export function boardPayload(dim) {
  const cells = {};
  for (const e of engines) {
    const c = dim.cells[e.id];
    cells[e.id] = { ...slimSummary(c), facets: c.facets.map(slimFacet), href: urls.engineDim(e.id, dim.id) };
  }
  return { id: dim.id, label: dim.label, long: dim.long, measure: measureOf(dim), facet_kind: dim.facet_kind,
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
    long: `${dim.long}: ${levelTitle(dim, level)}`, measure: measureOf(dim), facet_kind: rowKind(dim, level),
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
    return { id: d.id, label: d.label, long: d.long, measure: measureOf(d), cells, href: urls.dim(d.id) };
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
  "age": "Age", "disability": "Disability", "religion": "Religion", "nationality": "Nationality", "race": "Race", "sexuality": "Sexuality", "veteran": "Veteran", "family": "Family", "option-order": "Order" }[d.id] || d.label);

// ---------------------------------------------------------------------------------------------
// Words
// ---------------------------------------------------------------------------------------------
export const unit = (dim) => dim.raw_unit || " pts";
// A facet's own unit: a flip rate is a share of items even on a board that mixes it with shifts.
export const facetUnit = (dim, f) => (f && f.raw && f.raw.unit) || unit(dim);
// "%" results count texts whose answer changed ("X of every 100"); " pts" results measure how far
// the model's confidence moved, in percentage points.
export const isRate = (u) => String(u || "").trim() === "%";

// ---------------------------------------------------------------------------------------------
// Plain words for the sentences below, shared with cards.js and compliance.js.
// ---------------------------------------------------------------------------------------------
const q = (s) => `“${s}”`;
const an = (s) => (/^[aeiou]/i.test(s) ? "an" : "a");
// The gendered-wording word pairs are items of the gender board (assertive-bossy, agentic-communal, ...).
const GENDERED_ITEM = /^(assertive-bossy|direct-abrasive|confident-aggressive|calm-emotional|decisive-pushy|independent-selfish|agentic-communal)$/;
// The phrase a family-status test puts in front of the text, as a noun phrase after "As".
const FAMILY_CLAUSE = { married: "a married person", single: "a single person", divorced: "a divorced person",
  "single-parent": "a single parent", expecting: "a person expecting a baby" };
const familyClause = (g) => FAMILY_CLAUSE[g] || "a person";

// A decision's name inside a sentence: "surgeon / physician" -> "surgeon-or-physician".
const TASK_WORD = { "qpain-treatment": "prescribing", "civil-comments-moderation": "comment-removal",
  "tenant-inquiry-viewing": "apartment-viewing", "small-business-loan": "loan-approval",
  "resume-screening": "interview-screening", "cfpb-escalate-servicemember": "complaint-escalation",
  "cfpb-escalate-older": "complaint-escalation", "cfpb-escalate-family": "complaint-escalation",
  "assertive-bossy": "management-readiness", "direct-abrasive": "management-readiness",
  "confident-aggressive": "management-readiness", "calm-emotional": "management-readiness",
  "decisive-pushy": "management-readiness", "independent-selfish": "management-readiness",
  "agentic-communal": "advancement" };
export function taskWord(itemId, label) {
  if (TASK_WORD[itemId]) return TASK_WORD[itemId];
  if (!label) return "";
  return label.includes(" / ") ? label.split(" / ").map((x) => x.trim().replace(/\s+/g, "-")).join("-or-") : label;
}
// A decision's name as a label: "surgeon / physician" -> "surgeon or physician".
export const taskLabel = (label) => (label ? label.replace(/ \/ /g, " or ") : label);

// What the texts of a decision are.
const TEXT_NOUN = { "qpain-treatment": ["case description", "case descriptions"],
  "civil-comments-moderation": ["comment", "comments"],
  "tenant-inquiry-viewing": ["rental inquiry", "rental inquiries"],
  "small-business-loan": ["loan application", "loan applications"],
  "resume-screening": ["resume summary", "resume summaries"],
  "cfpb-escalate-servicemember": ["complaint", "complaints"], "cfpb-escalate-older": ["complaint", "complaints"],
  "cfpb-escalate-family": ["complaint", "complaints"] };
// The kind of text a decision reads, singular and plural. Biographies unless the decision says otherwise.
export const textNoun = (itemId) => (TEXT_NOUN[itemId] || ["bio", "bios"])[0];
export const textsWord = (itemId) => (TEXT_NOUN[itemId] || ["bio", "bios"])[1];
// The texts of a whole dimension: one word when every decision uses the same kind, else "texts".
export function textsOf(dim, itemId = null) {
  if (itemId) return textsWord(itemId);
  const kinds = new Set(dim.breakdown.items.map((i) => textsWord(i.id)));
  return kinds.size === 1 ? [...kinds][0] : "texts";
}

// What a row of a breakdown is called, for a reader: a task is a decision.
export const kindWord = (k) => (k === "task" ? "decision" : k || "group");

// The one change we make, as a "when ..." clause.
export function changeWhen(dim, groupId, itemId) {
  const g = groupId ? groupLabel(dim, groupId) : null;
  switch (dim.id) {
    case "religion":
    case "nationality":
      return `when a ${textNoun(itemId)} says ${q(g)}`;
    case "race":
      if (groupId === "black-first-name") return "when only a white-sounding first name becomes a Black-sounding one";
      if (itemId === "surgeon-physician") return `when a white-sounding full name becomes ${an(g)} ${g}-sounding one`;
      if (itemId === "civil-comments-moderation") return `when a comment opens ${q(`As ${an(g)} ${g} person,`)}`;
      if (["tenant-inquiry-viewing", "small-business-loan", "resume-screening"].includes(itemId))
        return "when only a white-sounding first name becomes a Black-sounding one";
      return `when the patient in the case description is ${g}, not white`;
    case "sexuality": return `when a comment opens ${q(`As ${an(g)} ${g.toLowerCase()} person,`)}`;
    case "veteran":
      if (itemId && itemId !== "qpain-treatment")
        return `when a ${textNoun(itemId)} opens ${q(`As a veteran of ${groupId === "navy" ? "the Navy" : "the Iraq war"},`)}`;
      return `when the patient is ${an(g)} ${g}`;
    case "family": return `when a ${textNoun(itemId)} opens ${q(`As ${familyClause(groupId)},`)}`;
    case "gender":
      if (itemId === "qpain-treatment") return "when the patient is a woman, not a man";
      if (GENDERED_ITEM.test(itemId || "")) return "when a sentence describes a woman with the harsher word, compared with a man";
      return "when only the pronouns change";
    case "age":
      if (["small-business-loan", "resume-screening", "cfpb-escalate-older"].includes(itemId))
        return `when a ${textNoun(itemId)} opens with an older age, not 34`;
      return "when a bio gives the age as 61, not 34";
    case "disability": return `when a ${["qpain-treatment", "civil-comments-moderation"].includes(itemId) ? "text" : textNoun(itemId)} says ${q("a wheelchair user")}`;
    case "option-order": return "when the two answer options swap places";
    default: return `when we change the ${dim.label.toLowerCase()}`;
  }
}

// The control a result is read against, in words, and whether it is already built into the number.
function controlOf(f, u) {
  const fl = f.floor || {};
  const v = fmt(fl.value);
  const moves = isRate(u) ? `it changes its answer on ${v} of every 100` : `its confidence moves ${v} percentage points`;
  const out = (built, text, sentence) => ({ built, text, sentence });
  if (fl.source === "none") return out(false, "no control was measured for this model, so we compare against zero",
    "No control was measured for this model, so we compare against zero.");
  if (fl.source === "ask-twice" || fl.source === "ask-twice-borrowed") {
    const t = `when we simply ask again about the same unchanged text, ${moves}${fl.source === "ask-twice-borrowed" ? " (measured on another decision)" : ""}`;
    return out(false, t, `By comparison, ${t}.`);
  }
  if (fl.source === "contrast") return out(true, "compared with the other groups, so a change every group shares is left out",
    "That is compared with the other groups, so a change every group shares is left out.");
  if (/version of the same/.test(fl.label || "")) return out(true, "measured against the otherwise identical case description, case by case",
    "That is measured against the otherwise identical case description, case by case.");
  if (fl.value === 0 && (fl.lo === null || fl.lo === undefined)) return out(true, "already measured against a harmless control edit, text by text",
    "That is already measured against a harmless control edit, text by text.");
  const t = `after a harmless control edit of the same size, ${moves}`;
  return out(false, t, `By comparison, ${t}.`);
}
export { controlOf };

// The range we are 95% sure of, in words.
export const sureBetween = (lo, hi) => `we are 95% sure the true figure is between ${fmt(lo)} and ${fmt(hi)}`;
const range = (lo, hi, d = 2) => `95% sure: ${fmt(lo, d)} to ${fmt(hi, d)}`;

export function verdictOf(f) {
  if (!f || f.status !== "measured") return { cls: "miss", text: "not measured" };
  if (!f.attributable) return { cls: "un", text: "every group moved alike" };
  if (f.detected) return { cls: "det", text: "a clear effect" };
  if (f.extra && f.extra.direction === "reverse") return { cls: "rev", text: "opposite of the stereotype" };
  return { cls: "nd", text: "no clear effect" };
}

const axisNoun = { religion: "religions", nationality: "nationalities", "name group": "name groups" };

// One sentence a lay reader can quote, for one engine on one cell.
export function cellSentence(dim, cell, engineId) {
  const f = cell.engines[engineId];
  const en = engineById[engineId].label;
  if (!f || f.status !== "measured") return `We have not tested ${en} here.`;
  const x = f.extra || {};
  const n = `${int(f.n)} ${textsOf(dim, cell.item)}`;
  if (dim.facet_kind === "question" || x.trope_consistent_answer != null) {
    const item = itemOf(dim, cell.item);
    const others = `one of the other ${axisNoun[dim.breakdown.group_kind] || "groups"}`;
    const ans = q(x.trope_consistent_answer);
    const lead = `When a bio opened with ${q(x.clause.trim().replace(/,$/, ""))}, ${en} was`;
    const asked = `to answer ${ans} to ${q(item.question)}`;
    if (f.detected) return `${lead} ${fmt(f.raw.value)} percentage points more likely ${asked} than when the bio named ${others}. That is the answer the stereotype predicts, and ${sureBetween(f.raw.lo, f.raw.hi)}.`;
    if (x.direction === "reverse") return `${lead} ${fmt(Math.abs(f.raw.value))} percentage points less likely ${asked} than when the bio named ${others}. That is the opposite of the stereotype. We are 95% sure the true difference is between ${fmt(f.raw.lo)} and ${fmt(f.raw.hi)} percentage points.`;
    return `${lead} about as likely ${asked} as when the bio named ${others}. The difference is between ${fmt(f.raw.lo)} and ${fmt(f.raw.hi)} percentage points, a range that includes zero, so there is no clear sign of the stereotype. We tested ${n}.`;
  }
  // An inserted clause ("A devout Muslim, ") is quoted; a whole-text version swap is described instead.
  if (x.signed_shift_pts !== undefined && x.floor_clause !== undefined && x.clause && /,\s*$/.test(x.clause)) {
    const lead = `With ${q(x.clause.trim().replace(/,$/, ""))} in place of ${q(x.floor_clause.trim().replace(/,$/, ""))}, ${en}'s confidence (its own probability) that the answer is ${q(x.positive)} ${x.signed_shift_pts < 0 ? "fell" : "rose"} by ${fmt(Math.abs(x.signed_shift_pts))} percentage points.`;
    const range2 = `We are 95% sure the true move is between ${fmt(x.signed_ci[0])} and ${fmt(x.signed_ci[1])}`;
    if (f.detected) return `${lead} ${range2}, so this is a clear effect. We tested ${n}.`;
    if (f.attributable) return `${lead} ${range2}, a range that includes zero, so this is not a clear effect. We tested ${n}.`;
    return `${lead} But every ${dim.breakdown.group_kind || "group"} moved about the same amount on this decision, so we cannot blame one ${dim.breakdown.group_kind || "group"}.`;
  }
  const u = facetUnit(dim, f);
  const item = itemOf(dim, cell.item);
  const task = taskWord(cell.item, item && item.label);
  const when = changeWhen(dim, cell.group, cell.item);
  const ctl = controlOf(f, u);
  const did = isRate(u)
    ? `${en} changes its ${task} answer on ${fmt(f.raw.value)} of every 100 ${textsOf(dim, cell.item)} ${when}.`
    : `${en}'s confidence (its own probability) in its ${task} answer moves ${fmt(f.raw.value)} percentage points ${when}.`;
  const gapWord = isRate(u) ? `${fmt(f.excess.value)} more of every 100` : `${fmt(f.excess.value)} percentage points`;
  const rangeText = `${sureBetween(f.excess.lo, f.excess.hi)}${f.detected ? "" : ", a range that includes zero"}`;
  if (!f.attributable) return `${did} ${ctl.sentence} Every ${dim.breakdown.group_kind || "group"} moved about the same, so we cannot blame this one.`;
  if (ctl.built) return `${did} ${ctl.sentence} ${f.detected ? "This is a clear effect" : "This is not a clear effect"}: ${rangeText}. We tested ${n}.`;
  return `${did} ${ctl.sentence} The difference, ${gapWord}, is ${f.detected ? "a clear effect" : "not a clear effect"}: ${rangeText}. We tested ${n}.`;
}

// The head of a board: what an engine's headline result measures, for the board lead.
function headOf(dim, board, engineId) {
  if (board === dim.board) return dim.cells[engineId];
  const level = dim.breakdown.levels.find((l) => l.board === board);
  return level ? level.heads[engineId] : null;
}

// A facet's name inside a sentence: a decision, a stereotype question or a group.
function facetName(dim, facetId, label) {
  const item = itemOf(dim, facetId);
  if (item && item.trope) return `the ${q(item.label)} question`;
  if (item) return `the ${taskWord(item.id, item.label)} decision`;
  return taskLabel(label);
}

// The page's lead number, for titles and descriptions.
export function boardLead(board, dim) {
  const top = board.ranked[0];
  if (top) {
    const head = headOf(dim, board, top.engine);
    const u = head && head.headline && head.headline.raw ? head.headline.raw.unit : unit(dim);
    const how = isRate(u) ? `changes its answer on ${fmt(top.value)} more of every 100 texts than after a harmless control edit`
      : `moves its confidence ${fmt(top.value)} percentage points more than a harmless control edit does`;
    return `${engineById[top.engine].label} shows the most bias: it ${how}, on ${facetName(dim, top.facet, top.facet_label)}`;
  }
  if (board.not_detected.length) {
    const ns = [...new Set(board.not_detected.map((r) => int(r.n)))];
    const level = dim.breakdown.levels.find((l) => l.board === board);
    return `No model shows a clear effect, in ${ns.join(" and ")} ${textsOf(dim, level && level.item)} tested`;
  }
  return "No model tested yet";
}

export function describeDim(dim) {
  const bd = dim.breakdown;
  const rows = `${bd.groups.length > 1 ? `${bd.group_kind} and ` : ""}${kindWord(bd.item_kind)}`;
  return `${dim.long}: how much each fast AI model changes its answers when we change only this detail, most biased first. ${boardLead(dim.board, dim)}. Results for every ${rows}, each with the range we are 95% sure of.`;
}

export function describeLevel(dim, level) {
  const t = levelTitle(dim, level);
  const lead = boardLead(level.board, dim);
  if (level.kind === "cell") {
    const cell = cellOf(dim, level.group, level.item);
    const first = level.board.ranked[0] || level.board.not_detected[0];
    return first ? cellSentence(dim, cell, first.engine) : `${dim.long}, ${t}: not tested yet.`;
  }
  const rows = level.kind === "group" ? `every ${kindWord(dim.breakdown.item_kind)}` : multiGroup(dim) ? `every ${dim.breakdown.group_kind}` : "every model";
  return `${dim.long}, ${t}: ${lead}. Results for ${rows}, with the range we are 95% sure of.`;
}

export { fmt, signed };

// The facet's own detail lines under its table row: every number the record carries beyond the
// headline measurement.
export function extraLines(dim, f) {
  const x = f.extra || {};
  const out = [];
  const pp = (v, d = 2) => `${signed(v, d)} percentage points`;
  if (x.direction_toward_more_female_pct !== undefined) out.push(`When the answer changed, it moved toward ${q((x.more_female_label || "").replace(/_/g, " "))} for the version that read as a woman ${fmt(x.direction_toward_more_female_pct, 1)} times in 100. Difference in how often it got the right answer for the two versions: ${pp(x.recall_gap_pts)}`);
  if (x.direction_share_pct !== undefined) out.push(`Of the ${x.n_flips} changed answers, ${fmt(x.direction_share_pct, 1)} in 100 moved toward physician for the Black name`);
  if (x.signed_shift_pts !== undefined && x.signed_ci) out.push(`Direction of the move${x.positive ? ` in its confidence in ${q(x.positive)}` : ""}: ${pp(x.signed_shift_pts)} (${range(x.signed_ci[0], x.signed_ci[1])})${x.flip_vs_floor_pct !== undefined ? `. Compared with the control edit, the answer itself changed on ${fmt(x.flip_vs_floor_pct)} of every 100 texts` : ""}`);
  if (x.floor_signed_shift_pts !== undefined) out.push(`The control edit alone moved it ${pp(x.floor_signed_shift_pts, 3)}`);
  if (x.all_sample) out.push(`Across all ${x.all_sample.n.toLocaleString("en-US")} bios: ${pp(x.all_sample.shift_pts, 3)} (${range(x.all_sample.ci[0], x.all_sample.ci[1], 3)}); the control edit ${pp(x.all_sample.floor_shift_pts, 3)}`);
  if (x.shift_61_minus_34_pts !== undefined) out.push(`Its confidence in “surgeon” at 61 minus at 34: ${pp(x.shift_61_minus_34_pts)} (${range(x.shift_ci[0], x.shift_ci[1])}). Changing 61 to 62, a control edit, changed the answer on ${fmt(x.floor_61_62_flip_pct)} of every 100 bios. When the answer changed, it called the older version “surgeon” ${fmt(x.direction_older_to_surgeon_pct, 1)} times in 100`);
  if (x.versions) out.push(Object.entries(x.versions).map(([r, v]) => `${cap(r)}: ${pp(v.shift_pts)} (${range(v.ci[0], v.ci[1])})`).join(" · "));
  if (x.shared_clause_pts !== undefined && x.shared_clause_pts !== null && x.shared_clause_ci) out.push(`Naming any ${dim.breakdown.group_kind || "group"} at all moved it ${pp(x.shared_clause_pts)} (${range(x.shared_clause_ci[0], x.shared_clause_ci[1])}). The ${plural(dim.breakdown.group_kind || "group")} differ from each other by up to ${fmt(x.spread_pts)}`);
  if (x.gender_flip_committed_pct !== undefined) out.push(`How often the answer changes when the pronouns swap: ${fmt(x.gender_flip_committed_pct)} of every 100 with the options in the usual order, ${fmt(x.gender_flip_reversed_pct)} with them reversed`);
  if (x.max_abs_dp !== undefined) out.push(`Largest change in its confidence on any one bio: ${fmt(x.max_abs_dp, 3)}, on a scale from 0 to 1`);
  if (x.group_mean_pct !== undefined) out.push(`Chance of answering ${q(x.trope_consistent_answer)} with ${q(x.clause.trim().replace(/,$/, ""))}: ${fmt(x.group_mean_pct)} in 100. With the control edit ${q(x.floor_clause.trim().replace(/,$/, ""))}: ${fmt(x.floor_mean_pct)} in 100. Difference: ${pp(x.shift_pts)} (${range(x.shift_ci[0], x.shift_ci[1])}). The yes-or-no answer changed on ${fmt(x.flip_pct)} of every 100 bios`);
  if (x.general_effect_pts !== undefined && x.general_effect_pts !== null) out.push(`Naming any ${dim.breakdown.group_kind || "group"} at all moved this answer ${pp(x.general_effect_pts)} (${range(x.general_effect_ci[0], x.general_effect_ci[1])}). That part is the same for every group, so it is left out of the stereotype score`);
  if (x.question && x.groups) out.push(`${q(x.question)} The answer that fits the stereotype: ${x.trope_consistent_answer}.`);
  if (x.groups) out.push(Object.entries(x.groups).map(([g, v]) => `${cap(g)} ${signed(v.trope_pts)} (${range(v.trope_ci[0], v.trope_ci[1])})${v.detected ? "*" : ""}`).join(" · ") + " (stereotype scores in percentage points; * a clear effect)");
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

// Which way a measured shift went: "up" when the model became more confident in the answer the test asks about (for
// example "yes, advance the candidate"), "down" when less, null where the result has no single direction.
export const dirOf = (f) => (f && f.extra && typeof f.extra.signed_shift_pts === "number" ? (f.extra.signed_shift_pts >= 0 ? "up" : "down") : null);
export const DIR_ARROW = { up: "\u25B2", down: "\u25BC" };
export const DIR_WORD = { up: "raised its confidence", down: "lowered its confidence" };

// One matrix cell: the most biased engine at that cell (or, with nothing detected, how the
// measured engines read), for the dimension page's group x item grid. With `engineId`, that
// engine's own value instead.
export function matrixCell(dim, cell, engineId = null) {
  const href = urls.at(dim, cell.group, cell.item);
  if (engineId) {
    const f = cell.engines[engineId];
    if (f.status !== "measured") return { status: "missing", href };
    return { status: "measured", engine: engineId, value: f.excess.value, lo: f.excess.lo, hi: f.excess.hi,
      detected: f.detected, attributable: f.attributable, reverse: !!(f.extra && f.extra.direction === "reverse"), dir: dirOf(f),
      href: `${href}#${engineId}`, prereg: cell.prereg };
  }
  const level = dim.breakdown.levels.find((l) => l.group === cell.group && l.item === cell.item &&
    (l.kind === "cell" || (!multiGroup(dim) && l.kind === "item") || (!multiItem(dim) && l.kind === "group")));
  const board = level ? level.board : null;
  const measured = engines.filter((e) => cell.engines[e.id].status === "measured");
  if (!measured.length) return { status: "missing", href, prereg: cell.prereg };
  const top = board && board.ranked[0];
  if (top) return { status: "measured", engine: top.engine, value: top.value, lo: top.lo, hi: top.hi, detected: true, dir: dirOf(cell.engines[top.engine]), href, prereg: cell.prereg, n_measured: measured.length };
  const best = measured.map((e) => ({ e, f: cell.engines[e.id] })).sort((a, b) => b.f.excess.value - a.f.excess.value)[0];
  const allReverse = measured.every((e) => cell.engines[e.id].extra && cell.engines[e.id].extra.direction === "reverse");
  return { status: "measured", engine: best.e.id, value: best.f.excess.value, lo: best.f.excess.lo, hi: best.f.excess.hi,
    detected: false, attributable: best.f.attributable, reverse: allReverse, dir: dirOf(best.f), href, prereg: cell.prereg, n_measured: measured.length };
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
    return { id: `${c.group || ""}/${c.item}`, label: labelOf(c), tag: null, href,
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
// Decisions that are not hiring: the age, disability and religion boards' hiring warning does not apply to them.
export const NON_HIRING_ITEMS = ["qpain-treatment", "civil-comments-moderation", "tenant-inquiry-viewing",
  "small-business-loan", "cfpb-escalate-servicemember", "cfpb-escalate-older", "cfpb-escalate-family"];
export const isNonHiring = (level) => !!(level && level.item && NON_HIRING_ITEMS.includes(level.item));
