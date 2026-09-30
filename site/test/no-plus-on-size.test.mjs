// Specs ensuring that size/excess values don't show a plus sign.
// Size values are never signed, so they should never be prefixed with "+".
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const DIST = fileURLToPath(new URL("../dist/", import.meta.url));

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out); else out.push(p);
  }
  return out;
}

test("lending table for nationality shows size values without plus signs", () => {
  const filePath = join(DIST, "nationality", "index.html");
  const html = readFileSync(filePath, "utf8");

  // Find the lending table by caption
  const tableMatch = html.match(/<caption[^>]*>Nationality lending decisions[^<]*nationalities[^<]*<\/caption>/);
  assert(tableMatch, "Found lending table caption");

  // Extract the table
  const tableStart = html.lastIndexOf("<table", tableMatch.index);
  const tableEnd = html.indexOf("</table>", tableStart) + 8;
  const table = html.substring(tableStart, tableEnd);

  // Should contain "4.57" (without plus)
  assert(table.includes("4.57"), "Table contains '4.57' value");

  // Should NOT contain "+4.57" (with plus)
  assert(!table.includes("+4.57"), "Table does not contain '+4.57' (plus-prefixed value)");

  // American row should contain down arrow
  assert(/<tr[^>]*>.*American.*▼.*<\/tr>/s.test(table), "American row contains down arrow");
});

test("no mx-v element contains a plus character", () => {
  const files = walk(DIST).filter(f => f.endsWith(".html"));
  for (const file of files) {
    const html = readFileSync(file, "utf8");

    // Find all mx-v spans
    const matches = [...html.matchAll(/<span class="mx-v"[^>]*>([^<]*)<\/span>/g)];
    for (const match of matches) {
      const content = match[1];
      assert(!content.includes("+"), `Found "+" in mx-v element in ${file}: "${content}"`);
    }
  }
});
