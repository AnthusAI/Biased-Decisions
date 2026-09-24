// Jersey 25 uses 30-unit steps, 750-unit capitals and a 1230-unit em.
// Give the scales the same 25-step capital height inside a 41-step em,
// with the base at the text baseline. CSS can then size the SVG to 1em.
import { writeFileSync } from "node:fs";

const pixels = new Set();
const rect = (x, y, w, h) => {
  for (let row = y; row < y + h; row++) {
    for (let col = x; col < x + w; col++) pixels.add(`${col},${row}`);
  }
};
const line = (x0, y0, x1, y1) => {
  const steps = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0));
  for (let i = 0; i <= steps; i++) {
    rect(Math.round(x0 + (x1 - x0) * i / steps), Math.round(y0 + (y1 - y0) * i / steps), 1, 1);
  }
};

rect(15, 2, 3, 22);
rect(14, 0, 5, 2);
for (let x = 6; x <= 26; x++) rect(x, Math.floor((x - 6) / 2), 1, 3);
for (const [cx, top] of [[6, 1], [26, 11]]) {
  line(cx, top, cx - 5, top + 7);
  line(cx, top, cx + 5, top + 7);
  rect(cx - 2, top + 5, 4, 4);
  rect(cx - 5, top + 9, 11, 1);
  rect(cx - 4, top + 10, 9, 1);
  rect(cx - 3, top + 11, 7, 1);
}
rect(12, 22, 9, 1);
rect(10, 23, 13, 1);
rect(8, 24, 17, 1);

// Merge adjacent pixels within each row so the vector has no raster seams.
const rows = Array.from({ length: 25 }, () => []);
for (const pixel of pixels) {
  const [x, y] = pixel.split(",").map(Number);
  rows[y].push(x);
}
let path = "";
rows.forEach((row, y) => {
  row.sort((a, b) => a - b);
  for (let i = 0; i < row.length;) {
    const start = row[i];
    let end = start;
    while (++i < row.length && row[i] === end + 1) end = row[i];
    const width = end - start + 1;
    path += `M${start + 4} ${y + 16}h${width}v1h-${width}z`;
  }
});
writeFileSync(new URL("../src/assets/scales.svg", import.meta.url),
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 41 41" width="1em" height="1em"><path fill="currentColor" d="${path}"/></svg>\n`);
