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
  assert.match(html, /reversed-statement and option-order control/);
  assert.match(html, /studies\/opinion-claims-antisemitism.jsonl/);
  assert.match(html, /studies\/adl-gaza-israel-hamas.jsonl/);
});
