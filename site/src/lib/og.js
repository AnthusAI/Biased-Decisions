// Open Graph images, rendered at build time: an SVG card per page, rasterised to PNG by resvg
// (WebAssembly, no native build step) with the site's own fonts, vendored under src/og/fonts
// (SIL Open Font License). If the fonts are missing the site still builds, without og:image.
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { engines } from "./site.js";

const FONT_DIR = resolve(process.cwd(), "src/og/fonts");
const FONTS = ["Jersey25-Regular.ttf", "Montserrat-SemiBold.ttf", "Montserrat-Regular.ttf"];
export const ogEnabled = FONTS.every((f) => existsSync(resolve(FONT_DIR, f)));

let ready = null;
async function resvg() {
  if (!ready) {
    ready = (async () => {
      const mod = await import("@resvg/resvg-wasm");
      const wasm = readFileSync(resolve(process.cwd(), "node_modules/@resvg/resvg-wasm/index_bg.wasm"));
      await mod.initWasm(wasm);
      return { Resvg: mod.Resvg, fonts: FONTS.map((f) => readFileSync(resolve(FONT_DIR, f))) };
    })();
  }
  return ready;
}

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// Greedy wrap by an average glyph width; good enough for a card, never overflows by much.
function wrap(text, size, width, maxLines, avg = 0.52) {
  const perLine = Math.max(8, Math.floor(width / (size * avg)));
  const words = String(text).split(/\s+/);
  const lines = [];
  let cur = "";
  for (const w of words) {
    if ((cur + " " + w).trim().length > perLine && cur) { lines.push(cur); cur = w; } else cur = (cur + " " + w).trim();
  }
  if (cur) lines.push(cur);
  if (lines.length > maxLines) {
    const kept = lines.slice(0, maxLines);
    kept[maxLines - 1] = kept[maxLines - 1].replace(/\s*\S*$/, "") + "…";
    return kept;
  }
  return lines;
}

export function cardSvg({ kicker = "", title, lead = "" }) {
  const W = 1200, H = 630, pad = 72;
  let tSize = 104;
  let tLines = wrap(title, tSize, W - 2 * pad, 2, 0.42);
  if (tLines.some((l) => l.length * tSize * 0.42 > W - 2 * pad) || tLines.length > 1) { tSize = 84; tLines = wrap(title, tSize, W - 2 * pad, 2, 0.42); }
  const lLines = wrap(lead, 30, W - 2 * pad, tLines.length > 1 ? 3 : 4, 0.53);
  const ty = 250;
  const ly = ty + (tLines.length - 1) * tSize * 0.95 + 70;
  const bars = engines.map((e, i) => `<rect x="${pad + i * 118}" y="${H - 64}" width="100" height="10" rx="3" fill="${e.color}"/>`).join("");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
<rect width="${W}" height="${H}" fill="#0c1e2b"/>
<rect x="0" y="0" width="${W}" height="8" fill="#d03382"/>
<text x="${pad}" y="104" font-family="Jersey 25" font-size="52" fill="#e8f2f8">Biased<tspan fill="#97a9b6"> Decisions</tspan></text>
<text x="${pad}" y="164" font-family="Montserrat" font-weight="600" font-size="24" letter-spacing="3" fill="#97a9b6">${esc(kicker.toUpperCase())}</text>
${tLines.map((l, i) => `<text x="${pad}" y="${ty + i * tSize * 0.95}" font-family="Jersey 25" font-size="${tSize}" fill="#ffffff">${esc(l)}</text>`).join("\n")}
${lLines.map((l, i) => `<text x="${pad}" y="${ly + i * 42}" font-family="Montserrat" font-size="30" fill="#bccbd6">${esc(l)}</text>`).join("\n")}
${bars}
<text x="${W - pad}" y="${H - 52}" text-anchor="end" font-family="Montserrat" font-weight="600" font-size="22" fill="#97a9b6">most biased first · every number replayed from the record</text>
</svg>`;
}

export async function renderPng(card) {
  const { Resvg, fonts } = await resvg();
  const r = new Resvg(cardSvg(card), { fitTo: { mode: "width", value: 1200 }, font: { fontBuffers: fonts, defaultFontFamily: "Montserrat", loadSystemFonts: false } });
  return r.render().asPng();
}
