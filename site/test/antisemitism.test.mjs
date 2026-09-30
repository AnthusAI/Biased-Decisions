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

test("the Gaza study identifies all three measured models and records", () => {
  const html = readFileSync(new URL("../dist/antisemitism-and-israel/index.html", import.meta.url), "utf8");

  assert.match(html, /Laya, Jev and Kev each directly assessed all 15 statements/);
  assert.match(html, /answers\/jev\/gaza-israel-hamas-decision-status/);
  assert.match(html, /answers\/kev\/gaza-israel-hamas-decision-status/);
  assert.match(html, /selected response/);
  assert.match(html, /no clear choice/);
  assert.match(html, /Probability strip legend/);
  assert.match(html, /class="probability-strip"/);
  assert.doesNotMatch(html, /Strongly agree: 0\.\d{4} · Somewhat agree/);
});

test("the nationality page keeps complete and legacy studies distinct", () => {
  const html = readFileSync(new URL("../dist/nationality/index.html", import.meta.url), "utf8");

  assert.match(html, /Lending decisions: all thirteen nationalities/);
  assert.match(html, /Stereotype questions: all thirteen nationalities/);
  assert.match(html, /Earlier stereotype questions: seven nationalities/);
  assert.doesNotMatch(html, /Israeli, greed: not tested/);
});
