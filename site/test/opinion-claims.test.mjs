import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("the opinion-claims hub publishes each measured model's recorded rates", () => {
  const html = readFileSync(new URL("../dist/opinion-claims/index.html", import.meta.url), "utf8");

  assert.match(html, /Results from the models we tested/);
  assert.match(html, /Anti-Jewish claims/);
  assert.match(html, /class="opinion-claim-family">Anti-Jewish claims<\/strong>/);
  assert.match(html, /class="opinion-claim-source">The Anti-Defamation League/);
  assert.match(html, /Laya/);
  assert.match(html, /Kev/);
  assert.match(html, /Jev/);
  assert.doesNotMatch(html, /No results published here yet/);
});
