import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("the antisemitism-and-israel hub lists the unpublished opinion-claims and adl-gaza arms", () => {
  const html = readFileSync(new URL("../dist/antisemitism-and-israel/index.html", import.meta.url), "utf8");

  assert.match(html, /Not shown yet/);
  assert.match(html, /Opinion and belief claims/);
  assert.match(html, /Direct statements about Gaza and Israel/);
  assert.match(html, /no control for how the model answers/);
  assert.match(html, /strongly agree.*for 13 of 15 statements/);
  assert.match(html, /contradict each other/);
  assert.match(html, /replaced by the controlled version above/);
  assert.match(html, /studies\/opinion-claims-antisemitism.jsonl/);
  assert.match(html, /studies\/adl-gaza-israel-hamas.jsonl/);
});

test("the controlled direct statements show a position only where the rule allows", () => {
  const html = readFileSync(new URL("../dist/antisemitism-and-israel/index.html", import.meta.url), "utf8");
  assert.match(html, /id="direct-statements"/);
  assert.match(html, /Direct statements, with controls/);
  assert.match(html, /No consistent position/);
  assert.match(html, /docs\/direct-statements-controlled-preregistration.md/);
});
