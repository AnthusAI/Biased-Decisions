import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const DIST = fileURLToPath(new URL("../dist/", import.meta.url));
const read = (path) => readFileSync(join(DIST, path), "utf8");
const text = (html) => html.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/g, " ")
  .replace(/<[^>]+>/g, " ").replace(/&[a-z#0-9]+;/g, " ").replace(/\s+/g, " ");

test("the methods page explains the withdrawn single-prompt arms and links their saved answers", () => {
  const html = read("methods/index.html");
  assert.match(html, /id="not-shown-yet"/);
  assert.match(html, /Opinion and belief claims/);
  assert.match(html, /Direct statements about Gaza and Israel/);
  assert.match(html, /contradict each other/);
  assert.match(html, /studies\/opinion-claims-antisemitism.jsonl/);
  assert.match(html, /studies\/adl-gaza-israel-hamas.jsonl/);
});

test("the controlled direct statements show a position only where the rule allows", () => {
  const html = read("antisemitism-and-israel/index.html");
  assert.match(html, /id="direct-statements"/);
  assert.match(html, /Direct statements, with controls/);
  assert.match(html, /No consistent position/);
  assert.doesNotMatch(html, /Not shown yet/);
});

// Pre-registration, plans and changes of plan belong on the methods page only.
const PROCESS = /pre-?regist\w*|study plan|plan written|written (down )?(first|before|in advance)|added after the answers|predictions? (were|was) not|deviation|addend|planned, not yet/i;

function pages(dir = DIST) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return pages(path);
    return name === "index.html" ? [path] : [];
  });
}

test("no page outside the methods page talks about our study plans or changes to them", () => {
  const offenders = [];
  for (const path of pages()) {
    const rel = path.slice(DIST.length);
    if (rel.startsWith("methods/")) continue;
    const html = readFileSync(path, "utf8");
    const m = PROCESS.exec(text(html));
    if (m) offenders.push(`${rel}: "${m[0]}"`);
  }
  assert.deepEqual(offenders.slice(0, 10), [], `${offenders.length} pages mention study plans`);
});
