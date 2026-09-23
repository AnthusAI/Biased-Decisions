// After the build: a small redirect page at every address the split religion and nationality
// dimensions used to have, so old links and shared cards still land. (Amplify serves real 301s
// from deploy/amplify-rules.json; these pages cover any host without them.)
import { readdirSync, statSync, mkdirSync, writeFileSync, existsSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const DIST = join(fileURLToPath(new URL("..", import.meta.url)), "dist");
export const MOVED = [["religion-v2", "religion"], ["stereotype-religion", "religion"], ["stereotype-nationality", "nationality"], ["race-fullname", "race"], ["race-name", "race"]];
const SITE = process.env.SITE_URL || "https://biased-decisions.anth.us";

function dirsUnder(root) {
  const out = [];
  const walk = (d) => {
    if (existsSync(join(d, "index.html"))) out.push(relative(DIST, d));
    for (const n of readdirSync(d)) { const p = join(d, n); if (statSync(p).isDirectory()) walk(p); }
  };
  if (existsSync(root)) walk(root);
  return out;
}

const page = (to) => `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Moved</title>
<link rel="canonical" href="${SITE}${to}"><meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url=${to}"></head><body><p>This page moved to <a href="${to}">${to}</a>.</p></body></html>
`;

export function writeLegacyRedirects() {
  let n = 0;
  const engines = existsSync(join(DIST, "engines")) ? readdirSync(join(DIST, "engines")).filter((e) => statSync(join(DIST, "engines", e)).isDirectory()) : [];
  for (const [oldId, newId] of MOVED) {
    const bases = [[newId, oldId], ...engines.map((e) => [`engines/${e}/${newId}`, `engines/${e}/${oldId}`])];
    for (const [from, to] of bases) {
      for (const dir of dirsUnder(join(DIST, from))) {
        const target = to + dir.slice(from.length);
        const file = join(DIST, target, "index.html");
        if (existsSync(file)) continue;
        mkdirSync(join(DIST, target), { recursive: true });
        writeFileSync(file, page(`/${dir}/`));
        n++;
      }
    }
  }
  return n;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) console.log(`legacy redirects: ${writeLegacyRedirects()} pages`);
