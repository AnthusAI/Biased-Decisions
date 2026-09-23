# Social preview cards

Every page of the leaderboard has its own Open Graph card: a 1200 x 630 PNG that states the
page's finding in numbers, so a link pasted into a feed, a chat or a slide says what the page
says. This file is the spec; `site/src/lib/cards.js` (the words and numbers) and
`site/src/lib/og.js` (the drawing) implement it, and `site/test/build.test.mjs` checks it against
the built site.

## How a card is made

- **At build time, statically.** An Astro endpoint per page (`site/src/pages/og/[...card].png.js`)
  lays the card out with Satori (flexbox to SVG, text converted to outlines) and rasterises it with
  resvg (WebAssembly build, so the same bytes come out on every machine). Nothing renders at
  request time.
- **Fonts are embedded**, pinned by `site/package-lock.json`: Jersey 25 (display) and Montserrat
  (text), from the `@fontsource/jersey-25` and `@fontsource/montserrat` packages (WOFF, latin
  subset). Both are under the SIL Open Font License 1.1; the licence texts ship in those packages.
- **Palette tokens from the site**: cards are light (ground `#f1f9fe`), board cards show horizontal bars most biased first, engine cards show a spider chart, and cell and engine-by-dimension cards keep one big number. Every text colour meets WCAG AA (4.5:1) on the ground; engine colours are used only for markers, never for text.

## Geometry

- 1200 x 630. The key content (who, and the number) sits in a central 630-wide column, so it
  survives the square crops some apps apply (WhatsApp, iMessage).
- Nothing smaller than about 40 px at full size, except the release stamp; the headline number
  is 100 px or larger.
- **At most three elements**: (1) the headline sentence, (2) the headline number with its floor,
  (3) the runners-up, or, on a pre-registered cell, whether the prediction held. The wordmark and
  the release stamp are furniture, not elements.
- Every card carries the release version and its date (or "unreleased"), small, top right.

## Addresses and caching

`/og/<page path>.<hash>.png`, for example `/og/stereotype-religion/jewish/greed.3f9a1c07e2.png`,
and `/og/index.<hash>.png` for the home page. The hash is the first 10 hex digits of the SHA-256
of everything the card shows (its words, numbers and release stamp) plus a layout version that is
bumped whenever `og.js` draws the same content differently, so a card's URL changes exactly when
its pixels do and social caches pick up new numbers. Cards are served with a
one-year immutable cache header.

## Templates

| page | headline (element 1) | number (element 2) | element 3 |
|---|---|---|---|
| home (`/`) | names the most biased engine on the overall board | its mean rank, with the number of contested dimensions | runners-up with their mean ranks |
| dimension (`/<dim>/`) | names the most biased engine on that board | its excess over the floor, the floor stated | runners-up; not-detected engines say "no bias detected at this floor" |
| group, question or task (`/<dim>/<a>/`) | what the most biased engine does there | its excess over the floor, the floor stated | runners-up, or the pre-registered prediction's outcome |
| group x question (`/<dim>/<group>/<item>/`) | what the most biased engine does in that cell | its excess over the floor, the floor stated | the pre-registered prediction's outcome where there is one, else runners-up |
| engine (`/engines/<engine>/`) | the engine's place on the overall board | its largest excess over any floor, the floor stated | where that excess is and how many dimensions were detected |
| engine x dimension (`/engines/<engine>/<dim>/`) | the engine's place on that board | its excess over the floor, the floor stated | how many of its questions or tasks cleared the floor |

| inversion (`/how-to-fail/`) | "How to cause a compliance failure with a fast decision model" | Laya's top-500 four-fifths ratio for women attorneys, the 0.80 line stated | the number of recipes, each tied to a measured result |
| guidance (`/guidance/`) | "Measuring and avoiding bias risk in fast decision models" | Laya's ratio after twin averaging, up from the ratio before | the checklist, every step linked to evidence |

Every page of a dimension mapped to a regulated practice (docs/leaderboard-architecture.md,
"Compliance") carries a **REGULATED DECISION** pill and an alarm-red top bar; its alt text adds
"Regulated decision: <practice>." The pill is furniture, like the release stamp, at 22 px. The
two compliance cards use the alarm red for the bar, the number and a warning triangle beside it.

The engines index uses the home template; the methods page has a card with no number, since it
reports none. Runners-up are capped at two rows (one beside a pre-registered outcome).

## Wording rules

- **The model is always the grammatical subject.** "Laya moves toward "greedy" when a bio says
  "Jewish": +0.74 pts". Never "Jewish -> greedy", which reads as a claim about people.
- **The floor is always shown** next to the number ("over a floor of 0.00 pts").
- **Not detected is never zero.** An engine whose interval includes the floor is "no bias
  detected at this floor", with its n; an unmeasured engine is "not measured".
- **Pre-registered cells** say whether the prediction held: "Pre-registered: the prediction
  held", "did not hold", or "not yet measured", quoting the verdict the data file carries.
- Numbers match the page to the digit (two decimals, as the tables show them).

## Accessibility and metadata

- Every page carries `og:image`, `og:image:width` 1200, `og:image:height` 630, `og:image:alt`,
  `twitter:card` `summary_large_image`, `twitter:image` and `twitter:image:alt`.
- The alt text is a data-driven sentence that carries the same numbers as the card (headline,
  number, floor, element 3, the prediction where one is quoted, and the release stamp), so a screen-reader user gets what a sighted reader
  gets. `og:title` is the card's headline and `og:description` the page's lead finding.
- Engines are told apart by marker shape (circle, square, diamond) and a direct label beside
  every marker, never by colour alone.

## Checks (`site/test/build.test.mjs`, run after `astro build`)

- Every page in `dist/` (except the 404 page and the redirect stubs) names an `og:image` that
  exists in `dist/`, is a PNG of exactly 1200 x 630 and is under 300 KB.
- Every card URL is fingerprinted (`.<10 hex digits>.png`) and no two pages share one.
- Every page states the floor its card quotes, so the alt-text check below holds.
- `og:image:alt` equals `twitter:image:alt`, and every number in it appears on the page.
- `/og-gallery/` (unlinked, `noindex`) shows every card at phone-feed width for review.
