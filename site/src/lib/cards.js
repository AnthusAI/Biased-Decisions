// The words and numbers on every page's social card (docs/social-cards.md). og.js draws them;
// Base.astro puts the card's URL, alt text, title and description in the page's metadata.
//
// A card is { template, headline, number?, numberNote?, bars?, rows[{engine?, text}], note?, stamp }:
// the headline (element 1), the number with the harmless edit it is read against, or bars
// (element 2), and a line or two of context (element 3). The model is always the grammatical
// subject and the sentence says what it did; a model whose range includes zero is "no clear
// effect", never zero. Words follow docs/plain-language.md.
import { categoryIntro, resultTitle, resultIntro, pageIntroductions } from "./introductions.js";
import { introModel } from "../pages/engines/_about.js";
import { createHash } from "node:crypto";
import { data, engines, engineById, dimensions, allDimensions, urls, levelPath, groupOf, itemOf, cellOf, multiGroup,
  multiItem, unit, fmt, signed, int, plural, largestBias, isNonHiring, cellOf as cellAt, facetUnit, isRate, taskWord, taskLabel,
  changeWhen, textsOf, kindWord } from "./site.js";

const rel = data.provenance.release;
export const STAMP = rel.released ? `v${rel.version} · ${rel.date}` : `v${rel.version} · unreleased`;

const E = (id) => engineById[id].label;
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
const lower = (s) => s.charAt(0).toLowerCase() + s.slice(1);
const ordinal = (n) => `${n}${n % 10 === 1 && n % 100 !== 11 ? "st" : n % 10 === 2 && n % 100 !== 12 ? "nd" : n % 10 === 3 && n % 100 !== 13 ? "rd" : "th"}`;
const q = (s) => `“${s}”`;

// The word a trope question pushes toward: what "yes" (or, for worldliness, "no") means.
const TROPE_WORD = { greed: "greedy", violence: "violent", arrogance: "arrogant",
  worldliness: "ignorant of the world", diligence: "hardworking", honesty: "honest" };

// What an engine does at one (group, item) position of a dimension, with the engine as subject:
// "Laya changes its paralegal-or-attorney answer when only the pronouns change".
export function doesAt(dim, groupId, itemId, engineId) {
  const en = E(engineId);
  const g = groupId ? groupOf(dim, groupId).label : null;
  const item = itemId ? itemOf(dim, itemId) : null;
  if (item && item.trope && g) return `${en} leans toward calling a person ${q(TROPE_WORD[itemId] || item.label)} when a bio says ${q(g)}`;
  const task = item ? taskWord(itemId, item.label) : null;
  const when = changeWhen(dim, groupId, itemId);
  const cell = itemId ? cellAt(dim, groupId, itemId) : null;
  const f = cell ? cell.engines[engineId] : null;
  const answer = task ? `its ${task} answer` : "its answer";
  if (isRate(facetUnit(dim, f))) return `${en} changes ${answer} ${when}`;
  return `${en} changes how sure it is of ${answer} ${when}`;
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

// The number's note: what the number counts, the harmless edit it is read against, and where.
const floorText = (dim, floorValue) => `percentage points beyond a harmless edit, which moved ${fmt(floorValue)}`;

// Runners-up from a board: every engine but the leader, ranked, then not detected, then missing.
function runners(board, skip, withN = true) {
  const rows = [];
  for (const r of board.ranked) if (r.engine !== skip) rows.push({ engine: r.engine, text: `${E(r.engine)} ${signed(r.value)} points` });
  for (const r of board.not_detected) if (r.engine !== skip) rows.push({ engine: r.engine, text: `${E(r.engine)}: no clear effect${withN ? `, in ${int(r.n)} texts` : ""}` });
  for (const id of board.unmeasured) if (id !== skip) rows.push({ engine: id, text: `${E(id)}: not tested` });
  return rows;
}

function barsOf(board, limit = 4) {
  const rows = [];
  for (const r of board.ranked) rows.push({ engine: r.engine, value: r.value, text: `${signed(r.value)}`, alt: `${signed(r.value)} percentage points` });
  for (const r of board.not_detected) rows.push({ engine: r.engine, value: 0, text: "no clear effect" });
  for (const id of board.unmeasured) rows.push({ engine: id, value: null, text: "not tested" });
  return rows.slice(0, limit);
}

// A board's card: the leader, its number over the floor, and the others.
function boardCard(template, dim, board, lead, floorValue, headlineFor, extra = {}, texts = "texts") {
  const top = board.ranked[0];
  if (top) {
    return { template, headline: headlineFor(top.engine), bars: barsOf(board), rows: [],
      numberNote: "percentage points more than after a harmless edit", ...extra };
  }
  const nd = board.not_detected;
  if (nd.length) {
    return { template, headline: `No model shows a clear effect on ${lead}`, number: int(nd[0].n),
      numberNote: nd.length > 1 ? `${texts} each; none clearly beyond a harmless edit` : `${texts}; not clearly beyond a harmless edit`,
      rows: runners(board, null, false), ...extra };
  }
  return { template, headline: `No model tested on ${lead} yet`, rows: runners(board, null), ...extra };
}

// At most two rows of runners-up (one beside a note), so element 3 fits.
function withRows(card, max = 2) {
  return { ...card, rows: card.rows.slice(0, card.note ? 1 : max) };
}

// ---------------------------------------------------------------------------------------------
// Templates
// ---------------------------------------------------------------------------------------------
function homeCard() {
  const rows = data.overall.rows;
  const top = rows[0];
  const bars = rows.map((r) => {
    const v = largestBias(r.engine);
    return { engine: r.engine, value: v, text: v > 0 ? `${signed(v)}` : "no clear effect", alt: v > 0 ? `${signed(v)} percentage points` : "no clear effect" };
  });
  return { template: "home", headline: `Of the fast AI models we tested, ${E(top.engine)} shows the most bias`,
    bars, rows: [], numberNote: "each model's largest bias, in percentage points" };
}

function dimCard(dim) {
  const lead = lower(dim.label);
  return boardCard("dimension", dim, dim.board, lead, (e) => dim.cells[e].headline.floor_value, (e) => {
    const tie = dim.board.ranked.filter((r) => r.value === dim.board.ranked[0].value).length > 1;
    if (!dim.board.contested) return `${E(e)}, the only model tested, shows bias on ${lead}`;
    return `${E(e)} ${tie ? "is tied for" : "shows"} the most bias on ${lead}`;
  }, {}, textsOf(dim));
}

function levelCard(dim, level) {
  const template = level.kind === "cell" ? "cell" : level.kind === "group" ? "group" : "item";
  const place = level.kind === "cell"
    ? `${groupOf(dim, level.group).label}, ${taskLabel(itemOf(dim, level.item).label)}`
    : level.kind === "group" ? groupOf(dim, level.group).label : taskLabel(itemOf(dim, level.item).label);
  const card = boardCard(template, dim, level.board, `${lower(dim.label)}: ${place}`,
    (e) => level.heads[e].headline.floor_value,
    (e) => { const [g, i] = positionOf(dim, level, level.heads[e]); return doesAt(dim, g, i, e); }, {}, textsOf(dim, level.item));
  return card;
}

function engineCard(en) {
  const rows = data.overall.rows;
  const i = rows.findIndex((r) => r.engine === en.id);
  const r = rows[i];
  const placeText = i === 0 ? `Of the ${rows.length} models we tested, ${en.label} shows the most bias`
    : `${en.label} ranks ${ordinal(i + 1)} of ${rows.length} models for bias, most biased first`;
  const detected = dimensions.filter((d) => d.cells[en.id].status === "measured" && d.cells[en.id].detected);
  const measured = dimensions.filter((d) => d.cells[en.id].status === "measured");
  if (!detected.length) {
    return { template: "engine", headline: placeText, number: fmt(r.mean_rank), numberNote: `average place, most biased first, over ${r.ranked_on} characteristics`,
      rows: [{ engine: en.id, text: `No clear effect on any of ${measured.length} characteristics` }] };
  }
  const top = detected.map((d) => ({ d, c: d.cells[en.id] })).sort((a, b) => b.c.headline.value - a.c.headline.value)[0];
  const axes = measured.map((d) => ({ label: d.label, value: d.cells[en.id].detected ? d.cells[en.id].headline.value : 0 }));
  return { template: "engine", headline: placeText, spider: { engine: en.id, axes },
    numberNote: `largest bias: ${signed(top.c.headline.value)} percentage points, on ${lower(top.d.label)}`,
    rows: [{ engine: en.id, text: `${en.label}, average place ${fmt(r.mean_rank)}` },
      { text: `A clear effect on ${detected.length} of ${measured.length} characteristics tested` }] };
}

function engineDimCard(en, dim) {
  const c = dim.cells[en.id];
  const lead = lower(dim.label);
  if (c.status !== "measured") {
    return { template: "engine-dim", headline: `${en.label} has not been tested on ${lead}`,
      rows: [{ engine: en.id, text: "Shown as missing, never as zero" }] };
  }
  const kind = plural(kindWord(dim.breakdown.item_kind));
  const count = { engine: en.id, text: `A clear effect on ${c.n_facets_detected} of ${c.n_facets} ${kind}` };
  const [g, it] = dimPositionOf(dim, en.id);
  if (!c.detected) {
    return { template: "engine-dim", headline: `${en.label} shows no clear effect on ${lead}`,
      number: int(c.n), numberNote: `${textsOf(dim, it)} tested; none clearly beyond a harmless edit`, rows: [count] };
  }
  const ranked = dim.board.ranked;
  const i = ranked.findIndex((r) => r.engine === en.id);
  const tie = ranked.filter((r) => r.value === ranked[i].value).length > 1;
  const above = ranked.filter((r) => r.value > ranked[i].value).length;
  const headline = !dim.board.contested ? `${en.label} is the only model tested on ${lead}`
    : above === 0 ? `${en.label} ${tie ? "is tied for" : "shows"} the most bias on ${lead}`
    : `${en.label} ranks ${ordinal(above + 1)}${tie ? " (tied)" : ""} of ${ranked.length + dim.board.not_detected.length} models for bias on ${lead}`;
  return { template: "engine-dim", headline, number: `${signed(c.headline.value)}`,
    numberNote: `${floorText(dim, c.headline.floor_value)}, on ${g ? `${groupOf(dim, g).label}, ` : ""}${it ? taskLabel(itemOf(dim, it).label) : taskLabel(c.headline.facet_label)}`,
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
    number: fmt(r.four_fifths_ratio), numberNote: `Laya's shortlist ratio for women attorneys; under ${fmt(COMP.shortlist.line)} is a warning sign`,
    rows: [{ text: `${COMP.recipes.length} ways to fail, each tied to a test result` }] };
}

function guidanceCard() {
  const before = shortRow("paralegal-attorney", "laya", "engine_alone", 500);
  const after = shortRow("paralegal-attorney", "laya", "twin_averaged", 500);
  return { template: "guidance", alarm: true, headline: "Measuring and avoiding bias risk in fast decision models",
    number: fmt(after.four_fifths_ratio), numberNote: `Laya's shortlist ratio when each bio is also read with the pronouns swapped, ${after.four_fifths_ratio > before.four_fifths_ratio ? "up" : "down"} from ${fmt(before.four_fifths_ratio)}`,
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

function finish(path, card, copy) {
  const c = { ...withRows(card), headline: copy.title, description: copy.intro, stamp: STAMP };
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
  if (c.bars) { if (c.numberNote) parts.push(`${cap(c.numberNote)}.`); for (const b of c.bars) parts.push(`${E(b.engine)}: ${b.alt || b.text}.`); }
  if (c.spider) { parts.push(`${cap(c.numberNote)}.`); parts.push(`Bias by characteristic: ${c.spider.axes.map((a) => `${a.label} ${a.value > 0 ? signed(a.value) + " percentage points" : "no clear effect"}`).join("; ")}.`); }
  for (const r of c.rows) parts.push(`${r.text}.`);
  parts.push(`Biased-Decisions leaderboard, ${c.stamp.replace(" · ", ", ")}.`);
  return parts.join(" ");
}

let cache = null;
export function allCards() {
  if (cache) return cache;
  const out = [];
  out.push(finish(urls.home(), homeCard(), pageIntroductions.home));
  out.push(finish(urls.engines(), titledCard("home", "Every model"), pageIntroductions.models));
  out.push(finish(urls.methods(), { template: "home", headline: "How every number on the leaderboard is made",
    rows: [{ text: "Change a personal detail. Compare the AI’s answers." }] }, pageIntroductions.methods));
  for (const en of engines) {
    out.push(finish(urls.engine(en.id), engineCard(en), { title: en.label, intro: `${introModel(en)} ${data.overall.rows.find((r) => r.engine === en.id).measured_on ? 'We test whether its judgments change when a text gives the same person a different gender, name or other personal detail.' : `We have not yet tested ${en.label}. No results are available yet.`}` }));
    for (const d of allDimensions) out.push(finish(urls.engineDim(en.id, d.id), flagged(d.id, engineDimCard(en, d)), { title: `${en.label} on ${d.label.toLowerCase()}`, intro: `${introModel(en)} ${d.cells[en.id].status === 'measured' ? categoryIntro(d).intro : `We have not tested ${en.label} on ${d.label.toLowerCase()} yet.`}` }));
  }
  for (const d of allDimensions) {
    out.push(finish(urls.dim(d.id), flagged(d.id, dimCard(d)), categoryIntro(d)));
    for (const level of d.breakdown.levels) out.push(finish(levelPath(d, level), flagged(d.id, levelCard(d, level), level), { title: resultTitle(d, level.group ? groupOf(d, level.group) : null, level.item ? itemOf(d, level.item) : null), intro: resultIntro(d, level.group ? groupOf(d, level.group) : null, level.item ? itemOf(d, level.item) : null) }));
  }
  out.push(finish(`${urls.home()}how-to-fail/`, inversionCard(), pageIntroductions.failure));
  out.push(finish(`${urls.home()}guidance/`, guidanceCard(), pageIntroductions.guidance));
  out.push(finish(`${urls.home()}stereotypes/`, { template: "guidance", alarm: false, rows: [{ text: "Eight sets of stereotype questions, each with its published sources" }] }, pageIntroductions.stereotypes));
  out.push(finish(`${urls.home()}antisemitism/`, { template: "guidance", alarm: false, rows: [{ text: "Six stereotypes, five ways of saying who the person is, three models" }] }, pageIntroductions.antisemitism));
  cache = out;
  return out;
}

export function cardFor(path) {
  return allCards().find((c) => c.path === path) || null;
}
