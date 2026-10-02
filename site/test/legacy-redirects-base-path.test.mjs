// Legacy redirect stubs must point inside the base path the site is built for, so the leaderboard
// can be served from a sub-path such as https://anth.us/biased-decisions/.
import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const SCRIPT_URL = new URL("../scripts/legacy-redirects.mjs", import.meta.url).href;

const stubFor = (targetPath, environment) =>
  execFileSync(
    process.execPath,
    ["--input-type=module", "-e", `import { legacyRedirectStub } from ${JSON.stringify(SCRIPT_URL)}; process.stdout.write(legacyRedirectStub(${JSON.stringify(targetPath)}));`],
    { env: { ...process.env, BASE_PATH: "", SITE_URL: "", ...environment }, cwd: fileURLToPath(new URL("..", import.meta.url)) },
  ).toString();

test("a redirect stub built under a base path points inside that base path", () => {
  const html = stubFor("/religion/", { BASE_PATH: "/biased-decisions/", SITE_URL: "https://anth.us" });
  assert.match(html, /<meta http-equiv="refresh" content="0; url=\/biased-decisions\/religion\/">/);
  assert.match(html, /<a href="\/biased-decisions\/religion\/">/);
  assert.match(html, /<link rel="canonical" href="https:\/\/anth\.us\/biased-decisions\/religion\/">/);
});

test("a base path without slashes is normalized", () => {
  const html = stubFor("/religion/", { BASE_PATH: "biased-decisions", SITE_URL: "https://anth.us" });
  assert.match(html, /url=\/biased-decisions\/religion\//);
});

test("a root build is unchanged", () => {
  const html = stubFor("/religion/", {});
  assert.match(html, /<meta http-equiv="refresh" content="0; url=\/religion\/">/);
  assert.match(html, /<link rel="canonical" href="https:\/\/biased-decisions\.anth\.us\/religion\/">/);
});
