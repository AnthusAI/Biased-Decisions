// Specs for the compliance pages and panels (BD-7ee753), run after `astro build`. They read
// dist/ and the data contract only. Each names the failure it prevents: a warning with no
// measured result behind it, a citation with no link, a deep link that lands nowhere, or a
// compliance page that does not say it is not legal advice.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";

// Decisions that are not hiring: pages for these carry no hiring warning (see NON_HIRING_ITEMS in site.js).
const NON_HIRING = ["qpain-treatment", "civil-comments-moderation", "tenant-inquiry-viewing", "small-business-loan",
  "cfpb-escalate-servicemember", "cfpb-escalate-older", "cfpb-escalate-family"];

const DIST = fileURLToPath(new URL("../dist/", import.meta.url));
const DATA = JSON.parse(readFileSync(new URL("../data/leaderboard.json", import.meta.url), "utf8"));
const C = DATA.compliance;

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out); else out.push(p);
  }
  return out;
}
const urlOf = (file) => "/" + relative(DIST, file).split(sep).join("/").replace(/index\.html$/, "");
const pages = new Map(walk(DIST).filter((f) => f.endsWith("index.html")).map((f) => [urlOf(f), readFileSync(f, "utf8")]).filter(([, h]) => !h.includes('http-equiv="refresh"')));
const unescape = (s) => s.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
const text = (html) => unescape(html.replace(/<script[\s\S]*?<\/script>/g, " ").replace(/<[^>]+>/g, " ")).replace(/\s+/g, " ");
const ids = (html) => new Set([...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]));

// The HTML of the element that opens at `start` (a tag with the given name), up to its matching close.
function element(html, start, tag) {
  const re = new RegExp(`<${tag}\\b|</${tag}>`, "g");
  re.lastIndex = start;
  let depth = 0, m;
  while ((m = re.exec(html))) {
    depth += m[0].startsWith("</") ? -1 : 1;
    if (depth === 0) return html.slice(start, m.index + m[0].length);
  }
  return html.slice(start);
}
function byId(html, id) {
  const m = new RegExp(`<(\\w+)[^>]*\\sid="${id}"`).exec(html);
  return m ? element(html, m.index, m[1]) : null;
}

// Where a link lands: the page must exist, and a fragment must name an element on it.
function landing(href, from) {
  const [path, frag] = href.split("#");
  const target = path === "" ? from : path;
  const html = pages.get(target);
  if (!html) return `${from} -> ${href}: no page`;
  if (frag && !ids(html).has(frag)) return `${from} -> ${href}: no #${frag} there`;
  return null;
}

const mapping = Object.fromEntries(C.mapping.map((m) => [m.dimension, m]));
const regulated = C.mapping.filter((m) => m.regulated).map((m) => m.dimension);
const dimOfPath = (p) => {
  const segs = p.split("/").filter(Boolean);
  if (segs[0] === "engines") return segs.length === 3 ? segs[2] : null;
  if (segs.slice(1).some((x) => NON_HIRING.includes(x))) return null;
  return DATA.dimensions.some((d) => d.id === segs[0]) ? segs[0] : null;
};
const primary = new Set(C.citations.map((c) => c.primary_url));

test("every page of a regulated dimension shows a red warning that is not colour alone", () => {
  let n = 0;
  for (const [path, html] of pages) {
    const dim = dimOfPath(path);
    if (!dim || !regulated.includes(dim)) continue;
    n++;
    const m = /<a class="reg-warn[^"]*" href="#risk" aria-label="([^"]+)"[^>]*>([\s\S]*?)<\/a>/.exec(html);
    assert.ok(m, `${path}: no warning linking to its risk panel`);
    assert.match(m[1], /^Regulated decision: /, `${path}: warning has no accessible name`);
    assert.match(m[2], /<svg[^>]*aria-hidden="true"/, `${path}: warning has no icon`);
    assert.match(text(m[2]), /Regulated decision/, `${path}: warning has no words`);
  }
  assert.ok(n > 100, `only ${n} regulated pages found`);
});

test("pages of an unregulated dimension carry no warning", () => {
  for (const [path, html] of pages) {
    const dim = dimOfPath(path);
    if (dim && !mapping[dim].regulated) assert.doesNotMatch(html, /class="reg-warn/, path);
  }
});

test("every risk panel links a measured result, a citation, a failure recipe and a guidance insight", () => {
  const recipes = new Set(C.recipes.map((r) => r.id));
  const insights = new Set(C.insights.map((i) => i.id));
  for (const [path, html] of pages) {
    const dim = dimOfPath(path);
    if (!dim || !regulated.includes(dim)) continue;
    const panel = byId(html, "risk");
    assert.ok(panel, `${path}: no risk panel`);
    assert.match(text(panel), /not legal advice/i, `${path}: panel does not say it is not legal advice`);
    const ev = [...panel.matchAll(/<a class="ev-link" href="([^"]+)"/g)].map((m) => m[1]);
    assert.ok(ev.length, `${path}: panel states no measured result`);
    for (const href of ev) assert.equal(landing(href, path), null);
    assert.match(text(panel), /between [−-]?\d+\.\d+ and [−-]?\d+\.\d+/, `${path}: panel quotes no interval`);
    assert.match(text(panel), /\d[\d,]* (?:bios|texts|comments|case descriptions|complaints|rental inquiries|loan applications|resume summaries|women)\b/, `${path}: panel quotes no sample size`);
    const cites = [...panel.matchAll(/<a class="cite" href="([^"]+)"/g)].map((m) => m[1]);
    assert.ok(cites.length, `${path}: panel cites no rule`);
    for (const c of cites) assert.ok(primary.has(c), `${path}: ${c} is not a verified citation`);
    const rec = [...panel.matchAll(/href="\/how-to-fail\/#([^"]+)"/g)].map((m) => m[1]);
    const ins = [...panel.matchAll(/href="\/guidance\/#([^"]+)"/g)].map((m) => m[1]);
    assert.ok(rec.length && ins.length, `${path}: panel links no recipe or no insight`);
    for (const r of rec) assert.ok(recipes.has(r), `${path}: unknown recipe ${r}`);
    for (const i of ins) assert.ok(insights.has(i), `${path}: unknown insight ${i}`);
  }
});

test("the inversion page grounds every recipe and gives each a stable anchor", () => {
  const html = pages.get("/how-to-fail/");
  assert.ok(html, "no /how-to-fail/ page");
  const t = text(html);
  assert.match(t, /not legal advice/i);
  assert.ok(t.includes(C.inversion.quote), "no Munger quote");
  assert.ok(html.includes(`href="${C.inversion.source_url}"`), "the quote is not sourced");
  for (const r of C.recipes) {
    const art = byId(html, r.id);
    assert.ok(art, `no #${r.id}`);
    const ev = [...art.matchAll(/<a class="ev-link" href="([^"]+)"/g)].map((m) => m[1]);
    assert.ok(ev.length >= r.evidence.length, `#${r.id}: ${ev.length} evidence links for ${r.evidence.length} entries`);
    for (const href of ev) {
      if (href.startsWith("http")) continue;
      assert.equal(landing(href, "/how-to-fail/"), null);
    }
    assert.ok(text(art).includes(r.inverse), `#${r.id}: no inverse practice`);
    assert.match(art, new RegExp(`href="/guidance/#${r.insight}"`), `#${r.id}: no guidance link`);
  }
});

test("the guidance page links every insight to its evidence and carries the checklist", () => {
  const html = pages.get("/guidance/");
  assert.ok(html, "no /guidance/ page");
  assert.match(text(html), /not legal advice/i);
  for (const i of C.insights) {
    const sec = byId(html, i.id);
    assert.ok(sec, `no #${i.id}`);
    const links = [...sec.matchAll(/<a class="ev-link" href="([^"]+)"/g)].map((m) => m[1]);
    assert.ok(links.length >= i.evidence.length, `#${i.id}: evidence not linked`);
    for (const href of links) if (!href.startsWith("http")) assert.equal(landing(href, "/guidance/"), null);
  }
  const list = byId(html, "checklist");
  assert.ok(list, "no checklist");
  for (const c of C.checklist) assert.ok(text(list).includes(c.text), c.text);
  for (const a of C.articles) assert.ok(html.includes(`href="${a.url}"`), a.url);
});

test("every evidence entry quoted on a page shows the record's number", () => {
  const fmt = (v) => Number(v).toFixed(2);
  const byEv = Object.fromEntries(C.evidence.map((e) => [e.id, e]));
  let n = 0;
  for (const [path, html] of pages) {
    for (const m of html.matchAll(/<li class="ev[^"]*" data-ev="([^"]+)"/g)) {
      const e = byEv[m[1]];
      assert.ok(e, `${path}: unknown evidence ${m[1]}`);
      const li = text(element(html, m.index, "li")).replace(/−/g, "-");
      if (e.kind === "cell") assert.ok(li.includes(`between ${fmt(e.lo)} and ${fmt(e.hi)}`) && li.includes(fmt(e.value)), `${path}: ${e.id} shows ${li}`);
      if (e.kind === "prereg") assert.ok(li.includes(e.observed.replace(/\*/g, "").slice(0, 20)), `${path}: ${e.id}`);
      n++;
    }
  }
  assert.ok(n > 0);
});

test("the shortlist is on its task pages, every row deep-linkable", () => {
  for (const block of C.shortlist.pairs) {
    const path = `/gender/${block.task}/`;
    const html = pages.get(path);
    const sec = byId(html, "shortlist");
    assert.ok(sec, `${path}: no #shortlist`);
    for (const r of block.rows) assert.ok(ids(html).has(`shortlist-${r.engine}-${r.variant.replace(/_/g, "-")}-${r.cut}`), `${path}: row ${r.engine} ${r.variant} ${r.cut}`);
    assert.match(text(sec), /four-fifths/);
  }
});

test("the home page points to the inversion and guidance pages and flags regulated dimensions", () => {
  const html = pages.get("/");
  assert.match(html, /href="\/how-to-fail\/"/);
  assert.match(html, /href="\/guidance\/"/);
  const flags = [...html.matchAll(/class="reg-warn compact"/g)].length;
  assert.ok(flags >= regulated.length, `${flags} compact flags for ${regulated.length} regulated dimensions`);
});

test("the masthead links the compliance pages from every page", () => {
  for (const [path, html] of pages) {
    if (path === "/og-gallery/" || !html.includes('class="topnav"')) continue;
    assert.match(html, /<nav class="topnav"[\s\S]*href="\/how-to-fail\/"[\s\S]*<\/nav>/, path);
  }
});

test("a page for the opioid or comment tasks carries no hiring warning", () => {
  let n = 0;
  for (const [path, html] of pages) {
    const segs = path.split("/").filter(Boolean);
    if (segs[0] === "engines" || !segs.slice(1).some((x) => NON_HIRING.includes(x))) continue;
    n++;
    assert.doesNotMatch(html, /class="reg-warn/, path);
  }
  assert.ok(n > 5, `only ${n} such pages found`);
});
