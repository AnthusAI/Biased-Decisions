import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

/**
 * Test that ensures every heading on the site makes the model (AI) the subject,
 * not a group of people. The rule is: say what the model did when a phrase
 * was inserted, not "people from X are Y". Stereotypes are described only in
 * note lines below headings, never in headings themselves. This test extracts
 * only h1-h4 text and checks for forbidden patterns there.
 *
 * Forbidden patterns (these should NOT appear as headings h1-h4):
 * - "the idea that <group> are/is..." (stereotypes phrased as facts about groups)
 * - "people/men/women/persons from/with..." (groups as the subject)
 * - "<group> are/is <negative trait>..." (direct assertions about groups)
 *
 * Positive examples (these SHOULD pass the test):
 * - "Dishonesty: what each model answered when the bio mentioned people from Henan province"
 * - "Muslim identity: what each model answered" (group name in phrase, not asserting about group)
 *
 * Negative examples (these SHOULD NOT appear as headings):
 * - "Muslims are dishonest" (group as subject with trait)
 * - "the idea that people from Henan are rough" (stereotype as fact)
 * - "People from China are lazy" (group as subject)
 */

const distPath = join(dirname(fileURLToPath(import.meta.url)), "..", "dist");

// Patterns that should NOT appear in headings
const forbiddenPatterns = [
  // Stereotype phrased as fact: "the idea that X are Y"
  /^the idea that /i,
  // Groups as subject with action: "people from X are...", "women are..."
  /^(people|persons?|men|women|folks|individuals?)\s+/i,
  // Group names followed by "are" or "is" (negative assertions)
  /^(chinese|japanese|indians?|africans?|arabs?|jews?|christians?|muslims?|uyghurs?|palestinians?|ukrainians?)\s+(people\s+)?(are|is)\s+/i,
  // Groups with "from" + trait: "people from X are Y"
  /^(people|persons?|men|women)\s+from\s+.+\s+(are|is)\s+/i,
  // Nationalities/groups as subject: "Henan people are...", "Shanghai residents are..."
  /^(.*\s+)?(people|residents|natives?|applicants?|candidates?|folks)\s+(are|is)\s+/i,
];

function walkDir(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) {
      if (name !== "_astro" && name !== "og" && name !== "data") walkDir(p, out);
    } else if (name === "index.html") out.push(p);
  }
  return out;
}

function extractHeadings(html) {
  const headings = [];
  const regex = /<h[1-4][^>]*>([^<]*)<\/h[1-4]>/gi;
  let match;
  while ((match = regex.exec(html)) !== null) {
    const text = match[1].trim();
    if (text) headings.push(text);
  }
  return headings;
}

test("no heading should phrase a stereotype as a fact about a group", () => {
  const htmlFiles = walkDir(distPath);
  const violations = [];

  for (const file of htmlFiles) {
    const html = readFileSync(file, "utf-8");
    const headings = extractHeadings(html);
    const relativePath = "/" + file.slice(distPath.length + 1).replace(/index\.html$/, "");

    for (const heading of headings) {
      for (const pattern of forbiddenPatterns) {
        if (pattern.test(heading)) {
          violations.push({
            file: relativePath,
            heading,
          });
          break; // Only report once per heading
        }
      }
    }
  }

  const report = violations.map((v) => `${v.file}: "${v.heading}"`).join("\n");
  assert.equal(
    violations.length,
    0,
    `Found ${violations.length} heading(s) that phrase a stereotype as a fact about a group (should say what the model did instead):\n${report}`
  );
});
