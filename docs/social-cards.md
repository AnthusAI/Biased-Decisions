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
- **Palette tokens from the site**: cards are light (ground `#f1f9fe`), board cards show horizontal bars most biased first, engine cards show a spider chart, and engine-by-characteristic cards keep one big number. Every text colour meets WCAG AA (4.5:1) on the ground; engine colours are used only for markers, never for text.

## Geometry

- 1200 x 630. The key content (who, and the number) sits in a central 630-wide column, so it
  survives the square crops some apps apply (WhatsApp, iMessage).
- Nothing smaller than about 40 px at full size, except the release stamp; the headline number
  is 100 px or larger.
- **At most three elements**: (1) the headline sentence, (2) the headline number with the harmless
  edit it is read against (or the bars), (3) one or two short lines of context. The wordmark and
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

Every card is written for someone who has never seen the site: it says which model, what it did,
and what the number counts. "Harmless edit" is the card's short name for the control edit: a change
of the same size that should not matter, such as adding "a keen cyclist".

| page | headline (element 1) | number (element 2) | element 3 |
|---|---|---|---|
| home (`/`) | "Of the fast AI models we tested, Laya shows the most bias" | bars: each model's largest bias, in percentage points | none |
| characteristic (`/<dim>/`) | the model that shows the most bias on that characteristic | bars: percentage points more than after a harmless edit; a model with nothing clear says "no clear effect" | none |
| group, question or decision (`/<dim>/<a>/`) | what the most biased model does there ("Laya changes its paralegal-or-attorney answer when only the pronouns change") | bars, as above | none |
| group x question (`/<dim>/<group>/<item>/`) | what the most biased model does in that square | bars, as above | none |
| engine (`/engines/<engine>/`) | the model's place among the models tested, most biased first | its largest bias in percentage points, and a spider chart by characteristic | its average place, and on how many characteristics it shows a clear effect |
| engine x characteristic (`/engines/<engine>/<dim>/`) | the model's place on that characteristic | its bias in percentage points, beyond a harmless edit (the harmless edit's own figure stated) | on how many of its decisions or questions it shows a clear effect |
| inversion (`/how-to-fail/`) | "How to cause a compliance failure with a fast decision model" | Laya's top-500 shortlist ratio for women attorneys, with "under 0.80 is a warning sign" | the number of ways to fail, each tied to a test result |
| guidance (`/guidance/`) | "Measuring and avoiding bias risk in fast decision models" | Laya's shortlist ratio when each bio is also read with the pronouns swapped, up from the ratio before | the checklist, every step linked to evidence |

When no model shows a clear effect, the headline says so ("No model shows a clear effect on age")
and the number is how many texts were tested, never zero.

Every page of a characteristic mapped to a regulated practice (docs/leaderboard-architecture.md,
"Compliance") carries a **REGULATED DECISION** pill and an alarm-red top bar; its alt text adds
"Regulated decision: <practice>." The pill is furniture, like the release stamp, at 22 px. The
two compliance cards use the alarm red for the bar, the number and a warning triangle beside it.

The engines index uses the home template; the methods page has a card with no number, since it
reports none. Runners-up are capped at two rows.

## Wording rules

The words follow docs/plain-language.md.

- **The model is always the grammatical subject, and the sentence says what it did.** "Laya leans
  toward calling a person "greedy" when a bio says "Jewish"". Never "Jewish -> greedy", which reads
  as a claim about people.
- **The harmless edit is always stated** next to a single number ("percentage points beyond a
  harmless edit, which moved 0.00").
- **Spell out "percentage points"**; never "pp" or "pts". Bars carry the bare signed number to fit,
  and the note under them names the unit; the alt text says "percentage points" on every bar.
- **No clear effect is never zero.** A model whose range includes zero is "no clear effect", with
  how many texts were tested; a model we did not run is "not tested".
- No hypothesis talk, no build talk: nothing about predictions, records or files.
- Numbers match the page to the digit (two decimals, as the tables show them).

## Accessibility and metadata

- Every page carries `og:image`, `og:image:width` 1200, `og:image:height` 630, `og:image:alt`,
  `twitter:card` `summary_large_image`, `twitter:image` and `twitter:image:alt`.
- The alt text is a data-driven sentence that carries the same numbers as the card (headline,
  number, the harmless edit's figure, element 3 and the release stamp), so a screen-reader user
  gets what a sighted reader gets. `og:title` is the card's headline and `og:description` the page's lead finding.
- Engines are told apart by marker shape (circle, square, diamond) and a direct label beside
  every marker, never by colour alone.

## Checks (`site/test/build.test.mjs`, run after `astro build`)

- Every page in `dist/` (except the 404 page and the redirect stubs) names an `og:image` that
  exists in `dist/`, is a PNG of exactly 1200 x 630 and is under 300 KB.
- Every card URL is fingerprinted (`.<10 hex digits>.png`) and no two pages share one.
- Every page states the harmless edit's figure its card quotes, so the alt-text check below holds.
- `og:image:alt` equals `twitter:image:alt`, and every number in it appears on the page.
- `/og-gallery/` (unlinked, `noindex`) shows every card at phone-feed width for review.
