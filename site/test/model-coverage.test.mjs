import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const DIST = new URL("../dist/", import.meta.url);
const DATA = JSON.parse(readFileSync(new URL("../data/leaderboard.json", import.meta.url), "utf8"));
const page = (path) => readFileSync(new URL(path, DIST), "utf8");
const readable = (html) => html.replace(/<script[\s\S]*?<\/script>/g, " ")
  .replace(/<[^>]+>/g, " ").replace(/&mdash;/g, "—").replace(/&amp;/g, "&")
  .replace(/\s+/g, " ");

function modelRow(html, id) {
  const link = new RegExp(`<a href="[^"]*/engines/${id}/"`).exec(html);
  assert.ok(link, `no model link for ${id}`);
  const start = html.lastIndexOf('<li class="ov-row', link.index);
  const end = html.indexOf("</li>", link.index);
  assert.ok(start >= 0 && end >= 0, `no model row for ${id}`);
  return html.slice(start, end + 5);
}

function placeText(row) {
  const match = /<div class="ov-place"[^>]*>([\s\S]*?)<\/div>/.exec(row);
  assert.ok(match, "model row has no place");
  return readable(match[1]).trim();
}

test("models without a rank are shown without a numeric place", () => {
  const home = page("index.html");
  const models = page("engines/index.html");
  for (const row of DATA.overall.rows.filter((r) => r.mean_rank === null)) {
    assert.equal(placeText(modelRow(home, row.engine)), "—", `${row.engine} on home`);
    assert.equal(placeText(modelRow(models, row.engine)), "—", `${row.engine} on models`);
  }
});

test("untested models are counted and described as not yet tested", () => {
  const rows = DATA.overall.rows;
  const tested = rows.filter((r) => r.measured_on > 0).length;
  const untested = rows.filter((r) => r.measured_on === 0);
  const home = page("index.html");
  const models = page("engines/index.html");
  const homeText = readable(home);
  const modelsText = readable(models);

  assert.ok(homeText.includes(`We compare ${tested} AI models`));
  assert.ok(modelsText.includes(`compare the ${tested} models tested so far`));
  for (const row of untested) {
    for (const [html, label] of [[home, "home"], [models, "models"]]) {
      const text = readable(modelRow(html, row.engine));
      assert.match(text, /not yet tested/i, `${row.engine} on ${label}`);
      assert.doesNotMatch(text, /no clear effect/i, `${row.engine} on ${label}`);
    }

    const detail = page(`engines/${row.engine}/index.html`);
    assert.match(detail, /<meta name="description" content="[^"]*not yet been tested/i);
    const detailText = readable(detail);
    assert.match(detailText, /No results are available because we have not yet tested/i);
    assert.doesNotMatch(detailText, /clear effect on 0/i);
  }
});
