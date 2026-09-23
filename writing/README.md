# Writing the site with Limatus

Everything a visitor reads on the site is written for one person: smart, new to this project, with no
machine learning background. `docs/plain-language.md` is the standard, with the word table.
[Limatus](https://github.com/AnthusAI/Limatus) checks the copy against it and never rewrites it for
you.

This follows the setup in `Anth.us` (a style profile, reference samples of approved prose, a rewrite
skill), tuned for a measurement site instead of a blog.

## What is here

| file | what it is |
|---|---|
| `style-profile.yml` | the house style as a checkable artifact: audience, tone, the words to avoid and prefer, the banned patterns (each with the plain replacement), density limits |
| `reference-samples/` | seven short passages of approved plain prose; Limatus reads them to learn the voice. Add to them when a passage is approved. |
| `editorial-rewrite-skill.yml` | the constraints for rewrite options: keep every number, never invent, define a term in the sentence |
| `pages.txt` | which built pages to scan: one per template plus every hand-written page |

## Checking the copy

```bash
make copy-check          # build the site, then scan every page in writing/pages.txt
python scripts/scan_copy.py --pages /gender/ /methods/     # a few pages
npm run check:plain --prefix site                          # the jargon test on every built page
```

The scan writes each page's readable text to `var/copy/<page>.md` and Limatus's findings beside it as
JSON. It reads the `../Limatus` checkout when there is one (set `LIMATUS_SRC` to point elsewhere),
because the profile uses keys newer than some installed releases.

## Working through findings

A finding is a question, not a verdict. For each one decide: **skip** (it is fine here), **rewrite**,
**delete** or **keep**. Record the decision with `limatus decide`, then ask for options only on the
ones marked rewrite:

```bash
limatus decide --finding-id finding-... --decision rewrite --note "explain floor" --decisions var/copy/decisions.json
limatus options --draft var/copy/gender.md --profile writing/style-profile.yml \
  --diagnosis var/copy/gender.json --decisions var/copy/decisions.json \
  --skill writing/editorial-rewrite-skill.yml
```

Most of the copy is not in a page file: it is in `biased_decisions/leaderboard.py` and `compliance.py`
(the descriptions, the risk panels, the guidance), in `site/src/pages/*.astro`, and in
`site/src/lib/*.js` (the sentences the site builds from the data). Rewrite it there, rebuild, scan again.

## The two checks, and what each is for

- **`plain-language.check.mjs`** is exact and cheap: it fails on the words in the word table, on every
  built page, including alt text and previews. It becomes part of `npm test` once the copy is clean.
- **Limatus** reads for what a word list cannot: a sentence that is hard to follow, a term that is
  never defined, a claim with nothing behind it, the same phrase repeated down a page.

Neither replaces reading the page as the person it is written for.
