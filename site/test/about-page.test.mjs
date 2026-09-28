import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const DIST = new URL("../dist/", import.meta.url);
const page = (path) => readFileSync(new URL(path, DIST), "utf8");
const readable = (html) => html.replace(/<script[\s\S]*?<\/script>/g, " ")
  .replace(/<[^>]+>/g, " ").replace(/&mdash;/g, "—").replace(/&amp;/g, "&")
  .replace(/\s+/g, " ");

test("About page exists in dist", () => {
  const aboutPage = page("about/index.html");
  assert.ok(aboutPage, "About page should exist");
});

test("Home page header and footer link to About", () => {
  const home = page("index.html");
  const text = readable(home);
  assert.match(text, /about/i, "home page should mention About");
  assert.ok(home.includes("about/"), "home page should link to /about/");
});

test("Methods page still builds", () => {
  const methods = page("methods/index.html");
  assert.ok(methods, "Methods page should exist");
  assert.match(readable(methods), /decision tests/i);
});

test("About page names each model and states Jev uses paid API access", () => {
  const about = page("about/index.html");
  const text = readable(about);

  // Check for model names
  assert.match(text, /jev/i, "About page should mention Jev");
  assert.match(text, /laya/i, "About page should mention Laya");
  assert.match(text, /kev/i, "About page should mention Kev");

  // Check for paid API access statement
  assert.match(text, /paid api access/i, "About page should mention paid API access for Jev");
});
