// The leaderboard is a static site: every page is generated at build time from
// data/leaderboard.json (written by `bd report --json`). No server runtime.
//
// SITE_URL is the public origin, used for canonical URLs and Open Graph tags (the deploy script
// sets it to the Amplify URL). BASE_PATH serves the site from a sub-path (GitHub Pages).
import { defineConfig } from "astro/config";

export default defineConfig({
  site: process.env.SITE_URL || "http://127.0.0.1:4321",
  base: process.env.BASE_PATH || "/",
  output: "static",
  trailingSlash: "always",
  build: { format: "directory" },
  devToolbar: { enabled: false },
  server: { host: "127.0.0.1", port: 4321 },
});
