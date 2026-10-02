// The wide-screen layout (the "Wide screens" block at the end of src/styles/site.css): every content
// section is split (a head that opens with its H2, then a body), prose, or an alarm panel split inside
// its border; no section is left unstructured; and the wide rules exist without touching laptops.
// Adapted from the Hard-Decisions site's test of the same name. Run after the build: it reads dist/.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";

const DIST = fileURLToPath(new URL("../dist/", import.meta.url));
const walk = (dir, out = []) => {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out); else out.push(p);
  }
  return out;
};
const pages = walk(DIST).filter((f) => f.endsWith("index.html"))
  .map((f) => ({ path: "/" + relative(DIST, f).split(sep).join("/").replace(/index\.html$/, ""), html: readFileSync(f, "utf8") }))
  // legacy redirect stubs carry no layout
  .filter((p) => !/<meta http-equiv="refresh"/i.test(p.html));
const sections = (html) => [...html.matchAll(/<section class="wrap section([^"]*)"[^>]*>([\s\S]*?)<\/section>/g)].map((m) => ({ cls: m[1], body: m[2].trim() }));
const FIGURE = /<(?:table|figure|svg|article|dl)\b|class="(?:[^"]*\s)?(?:dim-grid|spider-row|overall|table-scroll|chart-box)\b/;

test("every content section is split into a head and a body, marked as prose, or an alarm panel with its own head", () => {
  const bad = [];
  let split = 0, prose = 0, panel = 0;
  for (const p of pages) for (const s of sections(p.html)) {
    if (/\bsec-split\b/.test(s.cls)) {
      split++;
      const at = s.body.indexOf('<div class="sec-body">');
      if (!/^<div class="sec-head">\s*<h2\b/.test(s.body)) bad.push(`${p.path}: split section does not open with a head holding its H2`);
      if (at < 0) bad.push(`${p.path}: split section has no body`);
      else if (FIGURE.test(s.body.slice(0, at))) bad.push(`${p.path}: a figure, table or grid sits in a section head`);
    } else if (/\bsec-prose\b/.test(s.cls)) {
      prose++;
      if (/<h2\b/.test(s.body) && !/^<h2\b/.test(s.body)) bad.push(`${p.path}: a prose section's H2 is not its first child`);
    } else if (/\bsec-panel\b/.test(s.cls)) {
      panel++;
      if (!/^<div class="(?:reg-banner|risk-panel)">\s*<div class="sec-head">\s*<p class="risk-kicker">[\s\S]*?<h2\b[\s\S]*?<div class="sec-body">/.test(s.body)) bad.push(`${p.path}: an alarm panel does not hold a head (kicker and H2) and then a body`);
    } else bad.push(`${p.path}: section "${s.cls.trim()}" is neither split, prose nor a panel`);
  }
  assert.deepEqual(bad, []);
  assert.ok(split > 1000 && prose > 300 && panel > 50, `${split} split, ${prose} prose and ${panel} panel sections`);
});

test("the wide rules are in the stylesheet: column growth, zoom steps, the two-column split, the one-row hero and a line measure", () => {
  const css = readFileSync(new URL("../src/styles/site.css", import.meta.url), "utf8");
  assert.match(css, /@media \(min-width: 2000px\) \{[^}]*html \{ zoom: 1\.25; \}[^}]*:root \{ --max: 88%; \}/);
  assert.match(css, /@media \(min-width: 2800px\) \{ html \{ zoom: 1\.4; \} \}/);
  assert.match(css, /@media \(min-width: 4000px\) \{ html \{ zoom: 1\.6; \} \}/);
  assert.match(css, /@media \(min-width: 2400px\) \{\s*\.sec-split, \.sec-prose \{ display: grid; grid-template-columns: minmax\(0, 30%\) minmax\(0, 1fr\)/);
  assert.match(css, /\.sec-split > \.sec-head \{ position: sticky;/);
  assert.match(css, /\.hero:has\(\.hero-top\) \{ display: grid;/);
  assert.match(css, /\.section p, \.section li[^{]*\{ max-width: 36em; \}/);
  // Laptop and smaller layouts are untouched: no wide rule below 1,500 px.
  for (const m of css.matchAll(/@media \(min-width: (\d+)px\)[^{]*\{[^}]*(?:sec-split|sec-prose|sec-panel|zoom|--max)/g)) assert.ok(Number(m[1]) >= 1500, `wide rule at ${m[1]} px`);
});
