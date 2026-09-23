// The words and numbers on every page's social card (docs/social-cards.md). og.js draws them;
// Base.astro puts the card's URL, alt text, title and description in the page's metadata.
//
// A card is { template, headline, number?, numberNote?, rows[{engine?, text}], note?, stamp }:
// the headline (element 1), the number with its floor (element 2), and either runners-up or the
// pre-registered outcome (element 3). The model is always the grammatical subject; the floor is
// always stated; an engine whose interval includes the floor is "no bias detected at this floor",
// never zero.
import { createHash } from "node:crypto";
import { data, engines, engineById, dimensions, urls, levelPath, groupOf, itemOf, cellOf, multiGroup,
  multiItem, unit, fmt, signed, int, plural, largestBias, isNonHiring, NON_HIRING_ITEMS } from "./site.js";

const rel = data.provenance.release;
export const STAMP = rel.released ? `v${rel.version} · ${rel.date}` : `v${rel.version} · unreleased`;

const E = (id) => engineById[id].label;
const lower = (s) => s.charAt(0).toLowerCase() + s.slice(1);
const ordinal = (n) => `${n}${n % 10 === 1 && n % 100 !== 11 ? "st" : n % 10 === 2 && n % 100 !== 12 ? "nd" : n % 10 === 3 && n % 100 !== 13 ? "rd" : "th"}`;
const q = (s) => `“${s}”`;

// The word a trope question pushes toward: what "yes" (or, for worldliness, "no") means.
const TROPE_WORD = { greed: "greedy", violence: "violent", arrogance: "arrogant",
  worldliness: "ignorant of the world", diligence: "hardworking", honesty: "honest" };

// What an engine does at one (group, item) position of a dimension, with the engine as subject.
export function doesAt(dim, groupId, itemId, engineId) {
  const en = E(engineId);
  const g = groupId ? groupOf(dim, groupId).label : null;
  const task = itemId ? itemOf(dim, itemId).label : null;
  switch (dim.id) {
    case "religion":
    case "nationality":
      if (itemId && itemOf(dim, itemId).trope) return `${en} moves toward ${q(TROPE_WORD[itemId] || itemOf(dim, itemId).label)} when a bio says ${q(g)}`;
      return `${en} shifts its ${task} call when a bio says ${q(g)}`;
    case "race":
      if (groupId === "black-first-name") return `${en} flips its ${task} call when a white first name becomes a Black one`;
      if (itemId === "surgeon-physician") return `${en} shifts its ${task} call for ${g} full names`;
      return `${en} shifts its ${task} answer when the ${itemId === "civil-comments-moderation" ? "comment opens" : "vignette names"} ${g}`;
    case "sexuality": return `${en} shifts its comment-removal call when a comment opens "As a ${g.toLowerCase()} person,"`;
    case "veteran": return `${en} shifts its prescribing call for a ${g.toLowerCase()}`;
    case "gender":
      if (itemId === "qpain-treatment") return `${en} shifts its prescribing call when the vignette's patient is a woman`;
      return `${en} flips its ${task} call when the pronouns swap`;
    case "age": return `${en} flips its ${task} call when a bio says 61, not 34`;
    case "disability": return `${en} shifts its ${task} call when a ${NON_HIRING_ITEMS.includes(itemId) ? "text" : "bio"} says ${q("a wheelchair user")}`;
    case "option-order": return `${en} changes its ${task} call when the options swap places`;
    default: return `${en} moves on ${dim.label.toLowerCase()}${task ? `, ${task}` : ""}`;
  }
}

// The (group, item) a level head's headline facet points at.
export function positionOf(dim, level, head) {
  const f = head.headline.facet;
  if (level.kind === "cell") return [level.group, level.item];
  if (level.kind === "group") return [level.group, f];
  return multiGroup(dim) ? [f, level.item] : [null, level.item];
}
// The (group, item) of a dimension cell's headline facet (facets are items for two-axis
// dimensions, where the headline is the largest cell over the groups; see the architecture doc).
export function dimPositionOf(dim, engineId) {
  const c = dim.cells[engineId];
  const f = c.headline.facet;
  const bd = dim.breakdown;
  if (multiGroup(dim) && multiItem(dim)) {
    // A merged board's headline can name a group (a full-name group) as well as an item.
    if (bd.groups.some((g) => g.id === f)) {
      const inGroup = bd.cells.filter((x) => x.group === f && x.engines[engineId].status === "measured");
      const best = inGroup.sort((a, b) => b.engines[engineId].excess.value - a.engines[engineId].excess.value)[0];
      return [f, best ? best.item : bd.items[0].id];
    }
    const cells = bd.cells.filter((x) => x.item === f && x.engines[engineId].status === "measured");
    const top = cells.sort((a, b) => b.engines[engineId].excess.value - a.engines[engineId].excess.value)[0];
    return [top ? top.group : null, f];
  }
  if (multiGroup(dim)) return [f, bd.items[0] ? bd.items[0].id : null];
  return [null, f || (bd.items[0] && bd.items[0].id)];
}

const floorText = (dim, floorValue) => `over a floor of ${fmt(floorValue)}${unit(dim) === "%" ? "%" : " pts"}`;

// Runners-up from a board: every engine but the leader, ranked, then not detected, then missing.
function runners(board, skip, withN = true) {
  const rows = [];
  for (const r of board.ranked) if (r.engine !== skip) rows.push({ engine: r.engine, text: `${E(r.engine)} ${signed(r.value)} pts` });
  for (const r of board.not_detected) if (r.engine !== skip) rows.push({ engine: r.engine, text: `${E(r.engine)}: no bias detected at this floor${withN ? ` (n = ${int(r.n)})` : ""}` });
  for (const id of board.unmeasured) if (id !== skip) rows.push({ engine: id, text: `${E(id)}: not measured` });
  return rows;
}

function barsOf(board, limit = 4) {
  const rows = [];
  for (const r of board.ranked) rows.push({ engine: r.engine, value: r.value, text: `${signed(r.value)} pts` });
  for (const r of board.not_detected) rows.push({ engine: r.engine, value: 0, text: "no bias detected at this floor" });
  for (const id of board.unmeasured) rows.push({ engine: id, value: null, text: "not measured" });
  return rows.slice(0, limit);
}

// A board's card: the leader, its number over the floor, and the others.
function boardCard(template, dim, board, lead, floorValue, headlineFor, extra = {}) {
  const top = board.ranked[0];
  if (top) {
    return { template, headline: headlineFor(top.engine), bars: barsOf(board), rows: [],
      numberNote: `bias over each engine's own floor, in percentage points`, ...extra };
  }
  const nd = board.not_detected;
  if (nd.length) {
    return { template, headline: `No engine clears the floor on ${lead}`, number: `n = ${int(nd[0].n)}`,
      numberNote: nd.length > 1 ? "bios each; every interval includes the floor" : "bios; the interval includes the floor",
      rows: runners(board, null, false), ...extra };
  }
  return { template, headline: `No engine measured on ${lead} yet`, rows: runners(board, null), ...extra };
}

// At most two rows of runners-up (one beside a pre-registered outcome), so element 3 fits.
function withRows(card, max = 2) {
  return { ...card, rows: card.rows.slice(0, card.note ? 1 : max) };
}

// ---------------------------------------------------------------------------------------------
// Templates
// ---------------------------------------------------------------------------------------------
function homeCard() {
  const rows = data.overall.rows;
  const top = rows[0];
  const n = top.ranked_on;
  const bars = rows.map((r) => {
    const v = largestBias(r.engine);
    return { engine: r.engine, value: v, text: v > 0 ? `${signed(v)} pts` : "no bias detected at this floor" };
  });
  return { template: "home", headline: `${E(top.engine)} is the most biased engine on the overall board`,
    bars, rows: [], numberNote: `largest bias found, ranked over ${n} dimension${n === 1 ? "" : "s"}` };
}

function dimCard(dim) {
  const lead = lower(dim.long);
  return boardCard("dimension", dim, dim.board, lead, (e) => dim.cells[e].headline.floor_value, (e) => {
    const tie = dim.board.ranked.filter((r) => r.value === dim.board.ranked[0].value).length > 1;
    if (!dim.board.contested) return `${E(e)}, the only engine measured, is biased on ${lead}`;
    return `${E(e)} is ${tie ? "joint " : ""}most biased on ${lead}`;
  });
}

function levelCard(dim, level) {
  const template = level.kind === "cell" ? "cell" : level.kind === "group" ? "group" : "item";
  const place = level.kind === "cell"
    ? `${groupOf(dim, level.group).label} × ${itemOf(dim, level.item).label}`
    : level.kind === "group" ? groupOf(dim, level.group).label : itemOf(dim, level.item).label;
  const card = boardCard(template, dim, level.board, `${lower(dim.label)}: ${place}`,
    (e) => level.heads[e].headline.floor_value,
    (e) => { const [g, i] = positionOf(dim, level, level.heads[e]); return doesAt(dim, g, i, e); });
  return card;
}

function engineCard(en) {
  const rows = data.overall.rows;
  const i = rows.findIndex((r) => r.engine === en.id);
  const r = rows[i];
  const placeText = i === 0 ? `${en.label} is the most biased engine on the overall board`
    : `${en.label} places ${ordinal(i + 1)} of ${rows.length} on the overall board`;
  const detected = dimensions.filter((d) => d.cells[en.id].status === "measured" && d.cells[en.id].detected);
  const measured = dimensions.filter((d) => d.cells[en.id].status === "measured");
  if (!detected.length) {
    return { template: "engine", headline: placeText, number: fmt(r.mean_rank), numberNote: `mean rank over ${r.ranked_on} contested dimensions`,
      rows: [{ engine: en.id, text: `no bias detected at this floor on any of ${measured.length} dimensions` }] };
  }
  const top = detected.map((d) => ({ d, c: d.cells[en.id] })).sort((a, b) => b.c.headline.value - a.c.headline.value)[0];
  const axes = measured.map((d) => ({ label: d.label, value: d.cells[en.id].detected ? d.cells[en.id].headline.value : 0 }));
  return { template: "engine", headline: placeText, spider: { engine: en.id, axes },
    numberNote: `largest bias ${signed(top.c.headline.value)} pts, on ${lower(top.d.label)}`,
    rows: [{ engine: en.id, text: `${en.label}, mean rank ${fmt(r.mean_rank)}` },
      { text: `bias detected on ${detected.length} of ${measured.length} measured dimensions` }] };
}

function engineDimCard(en, dim) {
  const c = dim.cells[en.id];
  const lead = lower(dim.long);
  if (c.status !== "measured") {
    return { template: "engine-dim", headline: `${en.label} has not been measured on ${lead}`,
      rows: [{ engine: en.id, text: "Shown as missing, never as zero" }] };
  }
  const kind = plural(dim.breakdown.item_kind);
  const count = { engine: en.id, text: `${c.n_facets_detected} of ${c.n_facets} ${kind} clear the floor` };
  if (!c.detected) {
    return { template: "engine-dim", headline: `${en.label}: no bias detected at this floor on ${lead}`,
      number: `n = ${int(c.n)}`, numberNote: "bios; every interval includes the floor", rows: [count] };
  }
  const ranked = dim.board.ranked;
  const i = ranked.findIndex((r) => r.engine === en.id);
  const tie = ranked.filter((r) => r.value === ranked[i].value).length > 1;
  const above = ranked.filter((r) => r.value > ranked[i].value).length;
  const headline = !dim.board.contested ? `${en.label} is the only engine measured on ${lead}`
    : above === 0 ? `${en.label} is ${tie ? "joint " : ""}most biased on ${lead}`
    : `${en.label} places ${ordinal(above + 1)}${tie ? " (tied)" : ""} of ${ranked.length + dim.board.not_detected.length} on ${lead}`;
  const [g, it] = dimPositionOf(dim, en.id);
  return { template: "engine-dim", headline, number: `${signed(c.headline.value)} pts`,
    numberNote: `${floorText(dim, c.headline.floor_value)}, on ${g ? `${groupOf(dim, g).label} · ` : ""}${it ? itemOf(dim, it).label : c.headline.facet_label}`,
    rows: [count], biasNumber: true };
}

// ---------------------------------------------------------------------------------------------
// Compliance (BD-7ee753): a regulated-decision flag on every page whose decision maps to a
// regulated practice, and the inversion and guidance pages' own cards.
// ---------------------------------------------------------------------------------------------
const COMP = data.compliance;
const PRACTICE = Object.fromEntries(COMP.practices.map((p) => [p.id, p.label]));
const REG = Object.fromEntries(COMP.mapping.filter((m) => m.regulated).map((m) => [m.dimension, PRACTICE[m.practice]]));
export const flagFor = (dimId) => (REG[dimId] ? `Regulated decision: ${REG[dimId].toLowerCase()}` : null);
const flagged = (dimId, card, level = null) => (REG[dimId] && !isNonHiring(level) ? { ...card, flag: flagFor(dimId) } : card);
const shortRow = (task, engine, variant, cut) => COMP.shortlist.pairs.find((b) => b.task === task).rows
  .find((r) => r.engine === engine && r.variant === variant && r.cut === cut);

function inversionCard() {
  const r = shortRow("paralegal-attorney", "laya", "engine_alone", 500);
  return { template: "inversion", alarm: true, headline: "How to cause a compliance failure with a fast decision model",
    number: fmt(r.four_fifths_ratio), numberNote: `Laya's shortlist ratio, women attorneys; line ${fmt(COMP.shortlist.line)}`,
    rows: [{ text: `${COMP.recipes.length} recipes, each tied to a measured result` }] };
}

function guidanceCard() {
  const before = shortRow("paralegal-attorney", "laya", "engine_alone", 500);
  const after = shortRow("paralegal-attorney", "laya", "twin_averaged", 500);
  return { template: "guidance", alarm: true, headline: "Measuring and avoiding bias risk in fast decision models",
    number: fmt(after.four_fifths_ratio), numberNote: `Laya's ratio after twin averaging, from ${fmt(before.four_fifths_ratio)}`,
    rows: [{ text: "A checklist, every step linked to evidence" }] };
}

function titledCard(template, headline) {
  const base = homeCard();
  return { ...base, template, headline: `${headline}: ${base.headline}` };
}

// ---------------------------------------------------------------------------------------------
// Every page's card, by page path.
// ---------------------------------------------------------------------------------------------
// Bump LAYOUT when og.js draws the same content differently, so card URLs change with the pixels.
const LAYOUT = 7;
const hashOf = (card) => createHash("sha256").update(JSON.stringify({ LAYOUT, card })).digest("hex").slice(0, 10);

function finish(path, card) {
  const c = { ...withRows(card), stamp: STAMP };
  const hash = hashOf(c);
  const base = urls.home();
  const rel = path.slice(base.length).replace(/\/$/, "") || "index";
  return { ...c, path, hash, slug: `${rel}.${hash}`, url: `${base}og/${rel}.${hash}.png`, alt: altOf(c) };
}

// The alt text carries every word and number on the card, as sentences.
export function altOf(c) {
  const parts = [`${c.headline}${c.number ? `: ${c.number} ${c.numberNote}` : ""}.`];
  if (c.flag) parts.push(`${c.flag}.`);
  if (c.note) parts.push(`${c.note}.`);
  if (c.detail) parts.push(`${c.detail}.`);
  if (c.bars) { if (c.numberNote) parts.push(`${c.numberNote}.`); for (const b of c.bars) parts.push(`${E(b.engine)}: ${b.text}.`); }
  if (c.spider) { parts.push(`${c.numberNote}.`); parts.push(`Bias by dimension: ${c.spider.axes.map((a) => `${a.label} ${a.value > 0 ? signed(a.value) + " pts" : "none detected"}`).join("; ")}.`); }
  for (const r of c.rows) parts.push(`${r.text}.`);
  parts.push(`Biased-Decisions leaderboard, ${c.stamp.replace(" · ", ", ")}.`);
  return parts.join(" ");
}

let cache = null;
export function allCards() {
  if (cache) return cache;
  const out = [];
  out.push(finish(urls.home(), homeCard()));
  out.push(finish(urls.engines(), titledCard("home", "Every engine")));
  out.push(finish(urls.methods(), { template: "home", headline: "How every number on the leaderboard is made",
    rows: [{ text: "Change one detail of a real bio; read the change against an equally trivial edit" }] }));
  for (const en of engines) {
    out.push(finish(urls.engine(en.id), engineCard(en)));
    for (const d of dimensions) out.push(finish(urls.engineDim(en.id, d.id), flagged(d.id, engineDimCard(en, d))));
  }
  for (const d of dimensions) {
    out.push(finish(urls.dim(d.id), flagged(d.id, dimCard(d))));
    for (const level of d.breakdown.levels) out.push(finish(levelPath(d, level), flagged(d.id, levelCard(d, level), level)));
  }
  out.push(finish(`${urls.home()}how-to-fail/`, inversionCard()));
  out.push(finish(`${urls.home()}guidance/`, guidanceCard()));
  cache = out;
  return out;
}

export function cardFor(path) {
  return allCards().find((c) => c.path === path) || null;
}
