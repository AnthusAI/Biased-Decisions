// Specs ensuring that no browser script redeclares a name it imports.
// spider() once declared `const size`, shadowing the size() formatter from util.js; its tooltip
// then threw "size is not a function" and every spider chart rendered blank.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPTS = fileURLToPath(new URL("../src/scripts/", import.meta.url));

function importedNames(src) {
  const names = [];
  for (const m of src.matchAll(/^import\s*\{([^}]*)\}\s*from/gm)) {
    for (const part of m[1].split(",")) {
      const name = part.trim().split(/\s+as\s+/).pop();
      if (name) names.push(name);
    }
  }
  return names;
}

// Local declarations that would shadow `name`: const/let/var declarators (including later
// declarators in a comma list), function declarations, and function or arrow parameters.
function shadowingLines(src, name) {
  const n = name.replace(/[$]/g, "\\$");
  const declarator = new RegExp(`(?:\\b(?:const|let|var)\\s+|,\\s*)${n}\\s*=(?![=>])`);
  const fnDecl = new RegExp(`\\bfunction\\s+${n}\\b`);
  const param = new RegExp(`(?:^|[\\s,(])${n}\\s*(?:=[^=>][^,)]*)?(?=[,)])`);
  const paramLists = /function\s*\w*\s*\(([^()]*)\)|\(([^()]*)\)\s*=>/g;
  const hits = [];
  src.split("\n").forEach((line, i) => {
    if (/^\s*(?:import|\/\/)/.test(line)) return;
    const params = [...line.matchAll(paramLists)].some((m) => param.test(`(${m[1] ?? m[2]})`));
    if (declarator.test(line) || fnDecl.test(line) || params) hits.push(`${i + 1}: ${line.trim()}`);
  });
  return hits;
}

function shadows(src) {
  return importedNames(src).flatMap((name) => shadowingLines(src, name).map((l) => `${name} @ ${l}`));
}

test("the shadow check catches the spider() declaration that blanked the charts", () => {
  const src = [
    'import { fmt, size } from "./util.js";',
    "    const size = Math.min(w, compact ? 360 : 620);",
    "    const W = side, size = side - 12;",
    "function size(v) { return v; }",
    "const f = (a, size) => size;",
    "    const pad = compact ? 58 : side < 420 ? 70 : 104;",
    "    const tip = `${size(v.value)} points`;",
    "    if (size === 3) return;",
  ].join("\n");
  assert.deepEqual(shadows(src), [
    "size @ 2: const size = Math.min(w, compact ? 360 : 620);",
    "size @ 3: const W = side, size = side - 12;",
    "size @ 4: function size(v) { return v; }",
    "size @ 5: const f = (a, size) => size;",
  ]);
});

test("no browser script redeclares a name it imports", () => {
  for (const file of readdirSync(SCRIPTS).filter((f) => f.endsWith(".js"))) {
    const found = shadows(readFileSync(join(SCRIPTS, file), "utf8"));
    assert.deepEqual(found, [], `${file} redeclares an imported name:\n${found.join("\n")}`);
  }
});
