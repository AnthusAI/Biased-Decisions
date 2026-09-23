// Draws a social card (docs/social-cards.md): Satori lays out the card from lib/cards.js's words
// and numbers (text becomes outlines, with the fonts embedded), resvg rasterises it to a
// 1200 x 630 PNG. Both run at build time only.
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import satori from "satori";
import { engineById } from "./site.js";

const require = createRequire(import.meta.url);
const fontFile = (pkg, file) => readFileSync(require.resolve(`${pkg}/files/${file}`));

export const W = 1200;
export const H = 630;

// Palette tokens from site.css (dark ground), every text colour AA on the ground.
const C = { ground: "#0c1e2b", ink: "#e8f2f8", ink2: "#bccbd6", muted: "#97a9b6", floor: "#8a949c", rule: "#283b48", accent: "#e8579b",
  // The alarm red, only for regulated-decision cards; the ground's ink on it is AA.
  alarm: "#f5475e", onAlarm: "#0c1e2b" };

// The warning triangle, drawn in the alarm red with the ground showing through the exclamation.
const triangle = (size, fill, glyph) => ({ type: "svg", props: { width: size, height: size, viewBox: "0 0 20 20", style: { flexShrink: 0 },
  children: [{ type: "path", props: { d: "M10 1.6 19.2 18H.8Z", fill } }, { type: "path", props: { d: "M9 7h2v5.4H9zM9 13.8h2V16H9z", fill: glyph } }] } });

let fonts = null;
function loadFonts() {
  if (!fonts) {
    fonts = [
      { name: "Jersey 25", data: fontFile("@fontsource/jersey-25", "jersey-25-latin-400-normal.woff"), weight: 400, style: "normal" },
      { name: "Montserrat", data: fontFile("@fontsource/montserrat", "montserrat-latin-500-normal.woff"), weight: 500, style: "normal" },
      { name: "Montserrat", data: fontFile("@fontsource/montserrat", "montserrat-latin-600-normal.woff"), weight: 600, style: "normal" },
      { name: "Montserrat", data: fontFile("@fontsource/montserrat", "montserrat-latin-700-normal.woff"), weight: 700, style: "normal" },
    ];
  }
  return fonts;
}

let resvgReady = null;
async function resvg() {
  if (!resvgReady) {
    resvgReady = (async () => {
      const mod = await import("@resvg/resvg-wasm");
      await mod.initWasm(readFileSync(require.resolve("@resvg/resvg-wasm/index_bg.wasm")));
      return mod.Resvg;
    })();
  }
  return resvgReady;
}

// A tiny element builder for Satori's object form.
const el = (type, style, ...children) => ({ type, props: { style, children: children.flat().filter((c) => c !== null && c !== false && c !== undefined) } });

function marker(engineId, size) {
  const e = engineById[engineId];
  const fill = e.color_dark || e.color;
  const shape = e.marker === "square" ? { type: "rect", props: { x: 3, y: 3, width: 18, height: 18, rx: 2, fill } }
    : e.marker === "diamond" ? { type: "path", props: { d: "M12 1 L23 12 L12 23 L1 12 Z", fill } }
    : { type: "circle", props: { cx: 12, cy: 12, r: 10, fill } };
  return { type: "svg", props: { width: size, height: size, viewBox: "0 0 24 24", style: { flexShrink: 0 }, children: [shape] } };
}

// The card as a Satori tree. Key content (headline, number) sits in the central column.
export function cardTree(card) {
  const headSize = card.headline.length > 64 ? 44 : 48;
  const numberSize = 120;
  return el("div", { width: W, height: H, display: "flex", flexDirection: "column", alignItems: "center",
    backgroundColor: C.ground, color: C.ink, fontFamily: "Montserrat", padding: "34px 48px 30px", position: "relative" },
    // furniture: the wordmark and the release stamp
    el("div", { position: "absolute", top: 0, left: 0, width: W, height: card.alarm || card.flag ? 12 : 8, backgroundColor: card.alarm || card.flag ? C.alarm : C.accent, display: "flex" }),
    card.flag ? el("div", { position: "absolute", top: 38, left: 420, width: 360, height: 44, display: "flex", alignItems: "center", justifyContent: "center",
      gap: 10, backgroundColor: C.alarm, color: C.onAlarm, borderRadius: 8, fontSize: 22, fontWeight: 700, letterSpacing: 2 },
      triangle(24, C.onAlarm, C.alarm), "REGULATED DECISION") : null,
    el("div", { position: "absolute", top: 30, left: 48, display: "flex", fontFamily: "Jersey 25", fontSize: 44, color: C.ink },
      "Biased", el("span", { color: C.muted, marginLeft: 10 }, "Decisions")),
    el("div", { position: "absolute", top: 44, right: 48, display: "flex", fontSize: 24, fontWeight: 600, color: C.muted, letterSpacing: 1 }, card.stamp),
    // 1: headline
    el("div", { display: "flex", marginTop: 66, width: 660, justifyContent: "center", textAlign: "center",
      fontSize: headSize, fontWeight: 700, lineHeight: 1.14, color: C.ink }, card.headline),
    // 2: the number with its floor
    card.number ? el("div", { display: "flex", flexDirection: "column", alignItems: "center", marginTop: 8 },
      el("div", { display: "flex", alignItems: "center", gap: 24, fontFamily: "Jersey 25", fontSize: numberSize, lineHeight: 1, color: card.alarm ? C.alarm : "#ffffff" },
        card.alarm ? triangle(96, C.alarm, C.ground) : null, card.number),
      el("div", { display: "flex", fontSize: 40, fontWeight: 500, color: C.ink2, marginTop: 2, textAlign: "center" }, card.numberNote)) : null,
    // 3: the pre-registered outcome, or the runners-up
    el("div", { display: "flex", flexDirection: "column", alignItems: "center", marginTop: "auto", gap: 6 },
      card.note ? el("div", { display: "flex", fontSize: 40, fontWeight: 600, color: C.ink, textAlign: "center", maxWidth: 1100 }, card.note) : null,
      card.rows.map((r) => el("div", { display: "flex", alignItems: "center", fontSize: 40, fontWeight: 500, color: C.ink2, maxWidth: 1100 },
        r.engine ? marker(r.engine, 34) : null,
        el("span", { marginLeft: r.engine ? 14 : 0 }, r.text)))),
  );
}

export async function renderPng(card) {
  const svg = await satori(cardTree(card), { width: W, height: H, fonts: loadFonts() });
  const Resvg = await resvg();
  return new Resvg(svg, { fitTo: { mode: "width", value: W } }).render().asPng();
}
