import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("nationality lending pairs sections exist with correct structure", () => {
  const html = readFileSync(
    new URL("../dist/nationality/index.html", import.meta.url),
    "utf8"
  );

  // Check all three section ids exist
  assert.match(html, /id="nationality-lending-relative"/);
  assert.match(html, /id="nationality-lending-pairs"/);
  assert.match(html, /id="nationality-lending-flips"/);

  // Section A should have exactly 13 rows (one per nationality)
  const sectionA = html.match(
    /<section[^>]*id="nationality-lending-relative"[\s\S]*?<\/section>/
  )[0];
  const rowsInA = (sectionA.match(/<tr>/g) || []).length - 1; // -1 for header row
  assert.equal(rowsInA, 13, "Section A should have 13 nationality rows");

  // Section B should have 3 tables (one per engine), each 13x13
  const sectionB = html.match(
    /<section[^>]*id="nationality-lending-pairs"[\s\S]*?<\/section>/
  )[0];
  const matrices = sectionB.match(/<table class="matrix-pairs"[^>]*>/g);
  assert.equal(matrices.length, 3, "Section B should have 3 matrices");

  // Each matrix should have 13 body rows
  const bodyRows = sectionB.match(/<tbody>/g);
  assert.equal(bodyRows.length, 3, "Each matrix should have a tbody");

  // Count rows in each tbody - should be 13 each
  const tbodies = sectionB.match(/<tbody>[\s\S]*?<\/tbody>/g);
  for (let i = 0; i < tbodies.length; i++) {
    const rows = (tbodies[i].match(/<tr>/g) || []).length;
    assert.equal(
      rows,
      13,
      `Matrix ${i + 1} in section B should have 13 body rows`
    );
  }

  // Section C should mention borderline flips
  const sectionC = html.match(
    /<section[^>]*id="nationality-lending-flips"[\s\S]*?<\/section>/
  )[0];
  assert.match(sectionC, /Borderline applications/);

  // Laya's borderline flips should contain Palestinian with 34.8%
  assert.match(sectionC, /Palestinian[\s\S]*?34\.8%/);

  // No NaN or undefined anywhere on the page
  assert.doesNotMatch(html, /NaN/);
  assert.doesNotMatch(html, /undefined/);
});
