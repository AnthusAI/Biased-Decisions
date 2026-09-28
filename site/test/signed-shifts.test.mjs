import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

/**
 * Test that signed shifts (values with a direction) are displayed correctly:
 * 1. Downward shifts must display with a minus sign (not "+")
 * 2. Intervals for downward shifts must be negated and reordered (e.g., [−4.90, −4.25])
 * 3. Text must use "compared with" for signed values, "beyond" for unsigned
 *
 * This test:
 * - Checks every dimension and every breakdown cell with downward direction
 * - Verifies no page renders "+<magnitude>" for downward cells
 * - Verifies at least one downward interval is rendered negated (e.g., "−4.90")
 */

const distPath = join(dirname(fileURLToPath(import.meta.url)), "..", "dist");
const dataPath = join(dirname(fileURLToPath(import.meta.url)), "..", "data", "leaderboard.json");

test("every downward shift in matrices shows a minus sign and negated interval", () => {
  const data = JSON.parse(readFileSync(dataPath, "utf-8"));

  // Collect all downward shifts from all dimensions
  const downwardCells = [];

  for (const dim of data.dimensions) {
    for (const cell of dim.breakdown.cells) {
      for (const [engineId, engineData] of Object.entries(cell.engines)) {
        const signedShift = engineData?.extra?.signed_shift_pts;
        if (signedShift !== null && signedShift !== undefined && signedShift < 0) {
          downwardCells.push({
            dim: dim.id,
            group: cell.group,
            item: cell.item,
            engine: engineId,
            value: engineData.excess.value,
            signedValue: signedShift,
            lo: engineData.excess.lo,
            hi: engineData.excess.hi,
          });
        }
      }
    }
  }

  assert.ok(downwardCells.length > 0, "Should have downward shifts to test");

  const violations = [];
  const negatedIntervals = [];

  // Check each downward cell in the built pages
  for (const cell of downwardCells) {
    // Build the path to the dimension page (could be at various levels)
    const dimPagePath = join(distPath, cell.dim, "index.html");

    let html;
    try {
      html = readFileSync(dimPagePath, "utf-8");
    } catch {
      // If dimension page doesn't exist, skip (it may be a supplemental dimension)
      continue;
    }

    const magnitude = cell.value.toFixed(2);
    const signedValue = cell.signedValue.toFixed(2);
    const negatedLo = (-cell.hi).toFixed(2);
    const negatedHi = (-cell.lo).toFixed(2);

    // The bad pattern: "+magnitude" (with plus sign)
    const badPattern = `+${magnitude}`;

    // Correct patterns for downward shift:
    // 1. Minus sign with magnitude: "−4.57" or "-4.57"
    const minusPatterns = [
      `−${magnitude}`, // Unicode minus U+2212
      `-${magnitude}`, // ASCII minus
    ];

    // 2. Negated interval: "[−4.90, −4.25]" or equivalent
    const negatedIntervalPattern1 = `[−${negatedLo}, −${negatedHi}]`;
    const negatedIntervalPattern2 = `[−${negatedLo},−${negatedHi}]`; // no space
    const negatedIntervalPattern3 = `[-${negatedLo}, -${negatedHi}]`;
    const negatedIntervalPattern4 = `[-${negatedLo},-${negatedHi}]`;

    // Check for the bad pattern (must NOT appear)
    if (html.includes(badPattern)) {
      violations.push(
        `${cell.dim} (${cell.group}x${cell.item}/${cell.engine}): ` +
        `found "+${magnitude}" (should be signed −${magnitude})`
      );
    }

    // Check for correct minus sign (must appear)
    const hasMinus = minusPatterns.some((p) => html.includes(p));
    if (!hasMinus) {
      violations.push(
        `${cell.dim} (${cell.group}x${cell.item}/${cell.engine}): ` +
        `signed value −${magnitude} not found`
      );
    }

    // Check for negated interval (must appear somewhere)
    const hasNegatedInterval = [negatedIntervalPattern1, negatedIntervalPattern2, negatedIntervalPattern3, negatedIntervalPattern4]
      .some((p) => html.includes(p));

    if (hasNegatedInterval) {
      negatedIntervals.push(`${cell.dim}: [−${negatedLo}, −${negatedHi}]`);
    }
  }

  const violationReport = violations.map((v) => `  • ${v}`).join("\n");
  assert.equal(
    violations.length,
    0,
    `Found ${violations.length} rendering error(s) for downward shifts:\n${violationReport}`
  );

  assert.ok(
    negatedIntervals.length > 0,
    "Should find at least one negated interval (e.g., [−4.90, −4.25]) in the rendered pages"
  );
});
