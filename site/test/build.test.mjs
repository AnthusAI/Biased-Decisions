// Specs for the built site (run after `astro build`: `npm test` in site/). They read dist/ only.
// docs/social-cards.md and docs/leaderboard-architecture.md say what each one protects.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";

const DIST = fileURLToPath(new URL("../dist/", import.meta.url));
const DATA = JSON.parse(readFileSync(new URL("../data/leaderboard.json", import.meta.url), "utf8"));
const SITE = (process.env.SITE_URL || "https://biased-decisions.anth.us").replace(/\/$/, "");

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out); else out.push(p);
  }
  return out;
}
const files = walk(DIST);
const urlOf = (file) => "/" + relative(DIST, file).split(sep).join("/").replace(/index\.html$/, "");
const pages = files.filter((f) => f.endsWith("index.html")).map((f) => ({ file: f, path: urlOf(f), html: readFileSync(f, "utf8") }))
  .filter((p) => !p.html.includes('http-equiv="refresh"'));
const noindex = (p) => /<meta name="robots" content="noindex">/.test(p.html);
const content = pages.filter((p) => !noindex(p));

const unescape = (s) => s.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
function meta(html, key) {
  const re = new RegExp(`<meta (?:property|name)="${key.replace(/[.:]/g, "\\$&")}" content="([^"]*)"`);
  const m = re.exec(html);
  return m ? unescape(m[1]) : null;
}
function text(html) {
  const body = html.slice(html.indexOf("<body"));
  return unescape(body.replace(/<script[\s\S]*?<\/script>/g, " ").replace(/<[^>]+>/g, " ")).replace(/\s+/g, " ");
}
function pngSize(buf) {
  assert.equal(buf.toString("ascii", 1, 4), "PNG", "not a PNG");
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
}
const localPath = (url) => decodeURIComponent(new URL(url, SITE).pathname);

test("the build produced the pages the data file implies", () => {
  const levels = DATA.dimensions.reduce((n, d) => n + d.breakdown.levels.length, 0);
  // home, engines, methods, how-to-fail, guidance
  const expected = 1 + 1 + 1 + 2 + DATA.dimensions.length + levels + DATA.engines.length * (1 + DATA.dimensions.length);
  assert.equal(content.length, expected);
});

test("every page has a social card: a 1200 x 630 PNG under 300 KB, fingerprinted by content", () => {
  const seen = new Map();
  for (const p of content) {
    const img = meta(p.html, "og:image");
    assert.ok(img, `${p.path}: no og:image`);
    assert.ok(img.startsWith(`${SITE}/og/`), `${p.path}: og:image ${img} is not on ${SITE}`);
    assert.match(img, /\.[0-9a-f]{10}\.png$/, `${p.path}: card URL not fingerprinted`);
    assert.equal(meta(p.html, "twitter:image"), img);
    assert.equal(meta(p.html, "twitter:card"), "summary_large_image");
    assert.equal(meta(p.html, "og:image:width"), "1200");
    assert.equal(meta(p.html, "og:image:height"), "630");
    const file = join(DIST, localPath(img));
    assert.ok(existsSync(file), `${p.path}: ${img} is not in dist/`);
    const buf = readFileSync(file);
    assert.deepEqual(pngSize(buf), { width: 1200, height: 630 }, `${p.path}: card is not 1200 x 630`);
    assert.ok(buf.length < 300 * 1024, `${p.path}: card is ${Math.round(buf.length / 1024)} KB`);
    assert.ok(!seen.has(img), `${p.path} and ${seen.get(img)} share a card`);
    seen.set(img, p.path);
  }
});

test("card alt text is data-driven and every number in it is on the page", () => {
  const num = /[+−-]?\d[\d,]*(?:\.\d+)?/g;
  for (const p of content) {
    const alt = meta(p.html, "og:image:alt");
    assert.ok(alt && alt.length > 40, `${p.path}: no alt text`);
    assert.equal(meta(p.html, "twitter:image:alt"), alt, `${p.path}: twitter alt differs`);
    assert.ok(meta(p.html, "og:title"), `${p.path}: no og:title`);
    assert.ok(meta(p.html, "og:description"), `${p.path}: no og:description`);
    const page = text(p.html).replace(/−/g, "-");
    for (const n of alt.replace(/−/g, "-").match(num) || []) {
      const bare = n.replace(/^\+/, "").replace(/,$/, "");
      assert.ok(page.includes(bare), `${p.path}: alt text number ${n} is not on the page ("${alt}")`);
    }
    assert.doesNotMatch(alt, /→|->/, `${p.path}: alt text uses an arrow, not a sentence`);
  }
});

test("not detected is never written as zero on a card", () => {
  for (const p of content) {
    const alt = meta(p.html, "og:image:alt");
    assert.doesNotMatch(alt, /: 0(\.0+)? pts/, `${p.path}: ${alt}`);
  }
});

test("canonical and og:url name the public origin and the page's own path", () => {
  for (const p of content) {
    const canon = /<link rel="canonical" href="([^"]+)"/.exec(p.html)[1];
    assert.equal(canon, `${SITE}${p.path}`);
    assert.equal(meta(p.html, "og:url"), canon);
  }
});

test("the colophon names the release version and its date on every page", () => {
  const r = DATA.provenance.release;
  assert.ok(r && r.version, "the data file has no release version");
  for (const p of pages) {
    const colo = p.html.slice(p.html.indexOf('<footer class="colophon">'));
    assert.ok(colo.includes(`v${r.version}`), `${p.path}: no version in the colophon`);
    if (r.released) {
      assert.ok(colo.includes(r.date), `${p.path}: no release date in the colophon`);
      assert.ok(colo.includes(`https://github.com/AnthusAI/Biased-Decisions/releases/tag/${r.tag}`), `${p.path}: no release link`);
    } else {
      assert.ok(colo.includes("unreleased"), `${p.path}: no date and not marked unreleased`);
    }
    assert.ok(colo.includes(`/commit/${DATA.provenance.record_commit}`), `${p.path}: no commit link`);
  }
});

test("public pages never describe how the site or its charts were built", () => {
  const trivia = /hand-drawn|charting library|no charting|built with|\bastro\b|satori|resvg|webassembly|static site generator|drawn in the browser/i;
  for (const p of pages) assert.doesNotMatch(text(p.html), trivia, p.path);
});

test("every internal link resolves to a built page or file", () => {
  const missing = new Set();
  for (const p of pages) {
    for (const m of p.html.matchAll(/href="(\/[^"#?]*)(?:[#?][^"]*)?"/g)) {
      const path = decodeURIComponent(m[1]);
      const f = path.endsWith("/") ? join(DIST, path, "index.html") : join(DIST, path);
      if (!existsSync(f)) missing.add(`${p.path} -> ${path}`);
    }
  }
  assert.deepEqual([...missing], []);
});

test("every deep-link level has a page: each group, question and cell of every dimension", () => {
  const have = new Set(pages.map((p) => p.path));
  for (const want of ["/religion/jewish/greed/", "/nationality/american/", "/nationality/arrogance/",
    "/gender/nurse-physician/", "/race/black/", "/religion/jewish/paralegal-attorney/",
    "/engines/laya/nationality/", "/methods/", "/how-to-fail/", "/guidance/"]) assert.ok(have.has(want), want);
});

test("the first build's addresses still land: redirect stubs and the review gallery", () => {
  for (const f of ["dimension.html", "engine.html", "methods.html"]) assert.ok(existsSync(join(DIST, f)), f);
  const gallery = pages.find((p) => p.path === "/og-gallery/");
  assert.ok(gallery && noindex(gallery), "the card gallery is missing or indexable");
  const cards = [...gallery.html.matchAll(/<img src="([^"]+\.png)"/g)].map((m) => m[1]);
  assert.equal(new Set(cards).size, content.length, "the gallery does not show every card");
});

test("every page carries the caveats panel: four or six cards, open on the home page, folded elsewhere", () => {
  const n = DATA.honesty.length;
  assert.ok(n === 4 || n === 6, `${n} caveats: an odd count leaves an orphan card`);
  for (const p of content) {
    const m = /<details[^>]*id="read-first"[^>]*>([\s\S]*?)<\/details>/.exec(p.html);
    assert.ok(m, `${p.path}: no #read-first panel`);
    const cards = m[1].match(/<li class="caveat"/g) || [];
    assert.equal(cards.length, n, `${p.path}: ${cards.length} cards`);
    const open = /<details[^>]*id="read-first"[^>]*\bopen\b/.test(p.html);
    assert.equal(open, p.path === "/", `${p.path}: panel ${open ? "open" : "folded"}`);
    const panel = unescape(m[1].replace(/<[^>]+>/g, " ")).replace(/\s+/g, " ");
    for (const c of DATA.honesty) assert.ok(panel.includes(c.title), `${p.path}: missing "${c.title}"`);
  }
});

test("Google Analytics 4 tag is on every page, once, in the head", () => {
  const ID = "G-31SC26SDGX";
  for (const p of pages) {
    const head = p.html.slice(0, p.html.indexOf("</head>"));
    assert.equal(head.split(`googletagmanager.com/gtag/js?id=${ID}`).length - 1, 1, `${p.path}: gtag.js script`);
    assert.equal(head.split(`gtag('config', '${ID}')`).length - 1, 1, `${p.path}: gtag config`);
  }
});

test("the localStorage analytics opt-out script precedes the gtag config call on every page", () => {
  const script = "(function(){try{var k='anthus-no-analytics',q=location.search.match(/[?&]notrack=(\\w+)/);if(q){if(q[1]==='1')localStorage.setItem(k,'1');else localStorage.removeItem(k)}if(localStorage.getItem(k)==='1')window['ga-disable-G-31SC26SDGX']=true}catch(e){}})();";
  for (const p of pages) {
    const head = p.html.slice(0, p.html.indexOf("</head>"));
    assert.equal(head.split(script).length - 1, 1, `${p.path}: opt-out script`);
    assert.ok(head.indexOf(script) < head.indexOf("gtag('config'"), `${p.path}: opt-out must come before gtag config`);
  }
});
