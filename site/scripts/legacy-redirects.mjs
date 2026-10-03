// After the build: a small redirect page at every address the split religion and nationality
// dimensions used to have, so old links and shared cards still land. (Amplify serves real 301s
// from deploy/amplify-rules.json; these pages cover any host without them.)
import { readdirSync, statSync, mkdirSync, writeFileSync, existsSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const DIST = join(fileURLToPath(new URL("..", import.meta.url)), "dist");
export const MOVED = [["religion-v2", "religion"], ["stereotype-religion", "religion"], ["stereotype-nationality", "nationality"], ["race-fullname", "race"], ["race-name", "race"], ["gender-pronouns", "gender"], ["age-inserted", "age"], ["orientation", "sexuality"], ["gender-treatment", "gender", "root"], ["antisemitic-stereotypes-loan-narratives", "antisemitic-stereotypes-loan-narratives"], ["antisemitic-stereotypes", "antisemitic-stereotypes"], ["nationality-stereotypes", "nationality-stereotypes"], ["racial-and-ethnic-stereotypes", "racial-and-ethnic-stereotypes"], ["china-regional-stereotypes", "china-regional-stereotypes"], ["india-caste-and-regional-stereotypes", "india-caste-and-regional-stereotypes"], ["african-ethnic-stereotypes", "african-ethnic-stereotypes"], ["sexual-orientation-stereotypes", "sexual-orientation-stereotypes"], ["family-status-stereotypes", "family-status-stereotypes"]];
// The direct-statement arms' first, single-prompt version is described on the methods page.
export const PAGE_MOVES = [["opinion-claims", "/methods/#direct-statements"]];
const SITE = process.env.SITE_URL || "https://biased-decisions.anth.us";
const BASE_PATH_WITHOUT_TRAILING_SLASH = `/${(process.env.BASE_PATH || "/").replace(/^\/+|\/+$/g, "")}`.replace(/\/$/, "");

function dirsUnder(root) {
  const out = [];
  const walk = (d) => {
    if (existsSync(join(d, "index.html"))) out.push(relative(DIST, d));
    for (const n of readdirSync(d)) { const p = join(d, n); if (statSync(p).isDirectory()) walk(p); }
  };
  if (existsSync(root)) walk(root);
  return out;
}

export const legacyRedirectStub = (targetPathFromSiteRoot) => {
  const to = `${BASE_PATH_WITHOUT_TRAILING_SLASH}${targetPathFromSiteRoot}`;
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Moved</title>
<link rel="canonical" href="${SITE}${to}"><meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url=${to}"></head><body><p>This page moved to <a href="${to}">${to}</a>.</p></body></html>
`;
};

export function writeLegacyRedirects() {
  let n = 0;
  const engines = existsSync(join(DIST, "engines")) ? readdirSync(join(DIST, "engines")).filter((e) => statSync(join(DIST, "engines", e)).isDirectory()) : [];
  for (const [oldId, newId, rootOnly] of MOVED) {
    const bases = [[newId, oldId], ...engines.map((e) => [`engines/${e}/${newId}`, `engines/${e}/${oldId}`])];
    for (const [from, to] of bases) {
      for (const dir of dirsUnder(join(DIST, from))) {
        if (rootOnly && dir !== from) continue;
        const target = to + dir.slice(from.length);
        const file = join(DIST, target, "index.html");
        if (existsSync(file)) continue;
        mkdirSync(join(DIST, target), { recursive: true });
        writeFileSync(file, legacyRedirectStub(`/${dir}/`));
        n++;
      }
    }
  }
  // Single pages that moved to a section of another page.
  for (const [from, to] of PAGE_MOVES) {
    const file = join(DIST, from, "index.html");
    if (existsSync(file)) continue;
    mkdirSync(join(DIST, from), { recursive: true });
    writeFileSync(file, legacyRedirectStub(to));
    n++;
  }
  // Laya-mlx is one build of Laya now: its old pages land on Laya's.
  for (const dir of dirsUnder(join(DIST, "engines", "laya"))) {
    const target = dir.replace(/^engines\/laya/, "engines/laya-mlx");
    const file = join(DIST, target, "index.html");
    if (existsSync(file)) continue;
    mkdirSync(join(DIST, target), { recursive: true });
    writeFileSync(file, legacyRedirectStub(`/${dir}/`));
    n++;
  }
  return n;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) console.log(`legacy redirects: ${writeLegacyRedirects()} pages`);
