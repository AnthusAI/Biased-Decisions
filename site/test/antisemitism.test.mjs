import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("the antisemitism study has visual, source-by-source model comparisons", () => {
  const html = readFileSync(new URL("../dist/antisemitism/index.html", import.meta.url), "utf8");

  assert.match(html, /Visual comparison: real short professional biographies/);
  assert.match(html, /Visual comparison: made-up small-business loan narratives/);
  assert.match(html, /class="trope-visual"/);
  assert.match(html, /Largest clear score across the five wordings/);
  assert.match(html, /Jev/);
  assert.match(html, /Laya/);
  assert.match(html, /Kev/);
  assert.match(html, /Open every result on its own page/);
});
