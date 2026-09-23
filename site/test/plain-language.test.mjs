// The site is written for a reader who has never heard of this project. This test reads every built
// page the way a visitor does (visible text, link text, alt text, aria labels, titles, meta
// descriptions) and fails on words that only make sense to the people who built it. The style guide
// is docs/plain-language.md; the replacement for each word is there.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const DIST = join(dirname(fileURLToPath(import.meta.url)), "..", "dist");

// word or phrase -> what to say instead (see docs/plain-language.md)
const JARGON = [
  [/\bengines?\b/i, "model"],
  [/\bcues?\b/i, "edit / the change we make"],
  [/\bfloors?\b/i, "control edit"],
  [/\bexcess\b/i, "beyond the control edit"],
  [/\btropes?\b/i, "stereotype"],
  [/\bflip rates?\b/i, "how often the answer changes"],
  [/\bflips?\b|\bflipped\b/i, "changes"],
  [/\bvignettes?\b/i, "case description"],
  [/\btwins?\b/i, "swapped copy"],
  [/\bpp\b/i, "percentage points"],
  [/\btie-fair\b/i, "explain in words"],
  [/\bdimensions?\b/i, "characteristic / kind of bias"],
  [/\bmean rank\b/i, "average place"],
  [/\breplay(?:ed|s)?\b/i, "re-run from the saved answers"],
  [/\bbootstrap(?:ped)?\b|\bresamples?\b/i, "say what it is for, or drop it"],
  [/\bcorpus\b/i, "dataset"],
  [/\bfacets?\b/i, "part / result"],
  [/\bunattributed\b|\battributable\b/i, "say why in words"],
  [/\bpre-?regist\w*\b/i, "drop it (results first)"],
  [/\bbatch[- ]?\d\b/i, "drop it"],
  [/\bmeasured cells?\b|\bcells?\b/i, "results / squares"],
  [/\bstimul(?:us|i)\b/i, "the text we changed"],
  [/\bcounterfactuals?\b/i, "the same text with one word swapped"],
  [/\bsystem 1\b|\bnoul\b/i, "drop it"],
];

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) { if (name !== "_astro" && name !== "og" && name !== "data") walk(p, out); }
    else if (name === "index.html") out.push(p);
  }
  return out;
}

const decode = (s) => s.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;|&#x27;/g, "'").replace(/&nbsp;/g, " ");

// What a person can read on the page: text nodes and the attributes screen readers and previews use.
function readable(html) {
  const attrs = [...html.matchAll(/\b(?:alt|aria-label|title)="([^"]*)"/g)].map((m) => m[1]);
  const metas = [...html.matchAll(/<meta[^>]+(?:name|property)="(?:description|og:title|og:description|og:image:alt|twitter:image:alt)"[^>]+content="([^"]*)"/g)].map((m) => m[1]);
  let body = html.replace(/<(script|style|svg|code|pre)[\s\S]*?<\/\1>/gi, " ");
  body = body.replace(/<[^>]+>/g, " ");
  return decode([body, ...attrs, ...metas].join(" \n "));
}

test("no page uses words only the builders understand", () => {
  const found = new Map();
  for (const file of walk(DIST)) {
    const path = "/" + file.slice(DIST.length + 1).replace(/index\.html$/, "");
    if (/redirect|moved/i.test(readFileSync(file, "utf8").slice(0, 400)) && readFileSync(file, "utf8").includes('http-equiv="refresh"')) continue;
    const text = readable(readFileSync(file, "utf8"));
    for (const [re, say] of JARGON) {
      const m = re.exec(text);
      if (m) {
        const key = `${m[0].toLowerCase()} -> ${say}`;
        const entry = found.get(key) || { pages: [], sample: text.slice(Math.max(0, m.index - 50), m.index + 60).replace(/\s+/g, " ") };
        entry.pages.push(path);
        found.set(key, entry);
      }
    }
  }
  const report = [...found].map(([k, v]) => `${k}: ${v.pages.length} pages, e.g. ${v.pages[0]}  "...${v.sample}..."`).join("\n");
  assert.equal(found.size, 0, `\n${found.size} jargon terms on the site:\n${report}`);
});
