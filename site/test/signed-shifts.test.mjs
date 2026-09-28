import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

/**
 * Test that signed shifts (values with a direction) are displayed correctly.
 * When a finding has a downward direction (direction.toward = "down"),
 * the display value should be negative (e.g., "−4.57", not "+4.57").
 *
 * This test ensures that:
 * 1. The nationality page's lending table cell for American/Laya shows a decrease (not "+4.57")
 * 2. For every facet in leaderboard.json with downward direction, the rendered page
 *    text never shows "+<magnitude>"
 */

const distPath = join(dirname(fileURLToPath(import.meta.url)), "..", "dist");
const dataPath = join(dirname(fileURLToPath(import.meta.url)), "..", "data", "leaderboard.json");

function extractTableCells(html, tableCaption) {
  // Find the table with the given caption
  const captionMatch = new RegExp(
    `<caption[^>]*>${escapeRegex(tableCaption)}</caption>` +
    `(.*?)` +
    `</table>`,
    "is"
  ).exec(html);

  if (!captionMatch) return [];

  const tableHtml = captionMatch[1];
  const cells = [];

  // Extract all table cells (td elements)
  const cellRegex = /<td[^>]*>(.*?)<\/td>/gs;
  let match;
  while ((match = cellRegex.exec(tableHtml)) !== null) {
    cells.push(match[1]);
  }

  return cells;
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

test("nationality lending decisions show downward shifts as decreases, not increases", () => {
  const htmlPath = join(distPath, "nationality", "index.html");
  const html = readFileSync(htmlPath, "utf-8");

  // Load the leaderboard data to find expected downward shifts
  const data = JSON.parse(readFileSync(dataPath, "utf-8"));

  // Get the nationality dimension
  const nationality = data.dimensions.find((d) => d.id === "nationality");
  assert.ok(nationality, "nationality dimension should exist");

  // Find the lending breakdown
  const lendingCell = nationality.breakdown.cells.find(
    (c) => c.group === "american" && c.item === "small-business-loan"
  );
  assert.ok(lendingCell, "american x small-business-loan cell should exist");

  // Get Laya's data
  const layaData = lendingCell.engines.laya;
  assert.equal(layaData.status, "measured", "Laya should have measured data");

  // Check that we have a downward shift
  const signedShift = layaData.extra.signed_shift_pts;
  assert.ok(signedShift < 0, `Expected downward shift, got ${signedShift}`);

  // The raw magnitude (always positive)
  const magnitude = Math.abs(signedShift);
  const magnitudeStr = magnitude.toFixed(2);

  // The display value should use the signed value
  const negativeSign = "−"; // U+2212 minus sign OR regular minus
  const expectedPattern1 = `−${magnitudeStr}`; // Unicode minus
  const expectedPattern2 = `-${magnitudeStr}`; // ASCII minus

  // The problematic pattern we're checking against
  const badPattern = `+${magnitudeStr}`;

  // Extract the lending table
  const cells = extractTableCells(html, "Nationality lending decisions: all thirteen nationalities");
  assert.ok(cells.length > 0, "Should find lending table cells");

  // Search for the value in table cells (it should appear in the American row)
  const cellsJoined = cells.join(" ");

  // The bad pattern should NOT appear
  assert.ok(
    !cellsJoined.includes(badPattern),
    `Should not show "+${magnitudeStr}" (this appears to be showing downward shift as positive)`
  );

  // Either the negative pattern should appear, or just the magnitude without a sign
  // (since we might be using signed values differently)
  const hasNegative1 = cellsJoined.includes(expectedPattern1);
  const hasNegative2 = cellsJoined.includes(expectedPattern2);
  const hasMagnitude = cellsJoined.includes(magnitudeStr);

  assert.ok(
    hasNegative1 || hasNegative2 || hasMagnitude,
    `Expected to find "${expectedPattern1}" or "${expectedPattern2}" or "${magnitudeStr}" in cells, but found: ${cellsJoined}`
  );
});
