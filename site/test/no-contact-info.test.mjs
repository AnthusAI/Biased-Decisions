// Specs ensuring that contact information (email addresses) is not published.
// Runs after `astro build` and checks both the data file and built HTML.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const DIST = fileURLToPath(new URL("../dist/", import.meta.url));
const DATA = JSON.parse(readFileSync(new URL("../data/leaderboard.json", import.meta.url), "utf8"));

// Conservative regex matching email addresses: local@domain.tld
const EMAIL_PATTERN = /[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out); else out.push(p);
  }
  return out;
}

function findEmails(text) {
  return [...text.matchAll(EMAIL_PATTERN)].map(m => m[0]);
}

test("the data file contains no email addresses", () => {
  const dataJson = JSON.stringify(DATA);
  const emails = findEmails(dataJson);
  assert.deepEqual(emails, [], `Found email addresses in data file: ${emails.join(", ")}`);
});

test("no built HTML file contains email addresses", () => {
  const files = walk(DIST).filter(f => f.endsWith(".html"));
  for (const file of files) {
    const html = readFileSync(file, "utf8");
    const emails = findEmails(html);
    assert.deepEqual(emails, [], `Found email addresses in ${file}: ${emails.join(", ")}`);
  }
});
