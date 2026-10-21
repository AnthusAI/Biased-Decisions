# Writing the site with Humanus

Everything a visitor reads on the site is written for one person: smart, new to this project, with no
machine learning background. `docs/plain-language.md` is the standard, with the word table.
[Humanus](https://github.com/AnthusAI/Humanus) checks the copy against it and never rewrites it for
you.

This follows the setup in `Anth.us` (a style profile, reference samples of approved prose, a rewrite
skill), tuned for a measurement site instead of a blog.

## What is here

| file | what it is |
|---|---|
| `style-profile.yml` | the house style as a checkable artifact: audience, tone, the words to avoid and prefer, the banned patterns (each with the plain replacement), density limits. The scan converts it to a Humanus policy pack each run; edit the profile, not the pack. |
| `reference-samples/` | seven short passages of approved plain prose; they go into the policy pack as the voice to match. Add to them when a passage is approved. |
| `editorial-rewrite-skill.yml` | the constraints a rewrite must meet: keep every number, never invent, define a term in the sentence. Humanus no longer reads this file; use it to judge the options `humanus suggest` returns. |
| `pages.txt` | which built pages to scan: one per template plus every hand-written page |

## Checking the copy

```bash
make copy-check          # build the site, then scan every page in writing/pages.txt
python scripts/scan_copy.py --pages /gender/ /methods/     # a few pages
npm run check:plain --prefix site                          # just the jargon test, on every built page
```

Install Humanus with `make install`, or `pip install -e '.[copy]'` into an existing environment
(it is `humanus` on PyPI). The scan writes each page's readable text to `var/copy/<page>.md`,
Humanus's findings beside it as `var/copy/<page>.json`, and the policy pack it checked against as
`var/copy/pack.json`. To check one file by hand:

```bash
humanus pack import --profile writing/style-profile.yml > var/copy/pack.json
humanus check --draft var/copy/gender.md --pack var/copy/pack.json --format markdown
```

Each finding has an `id`, a `policyId` (such as `banned-patterns` or `avoid-lexicon`), a `severity`,
the `excerpt` it flags, a `message` and the `span` of the excerpt in the page text. Finding ids stay
the same across rescans while the sentence is unchanged.

## Working through findings

A finding is a question, not a verdict. For each one decide: **skip** (it is fine here), **rewrite**,
**delete** or **keep**. Humanus does not record decisions; note them in the Kanbus task for the
copy pass. Ask for rewrite options only on the ones marked rewrite (needs `OPENAI_API_KEY`):

```bash
jq -n --rawfile text var/copy/gender.md --slurpfile pack var/copy/pack.json \
  --slurpfile result var/copy/gender.json --arg id f-... \
  '{schemaVersion: 1, content: {format: "markdown", text: $text}, pack: $pack[0],
    finding: ($result[0].findings[] | select(.id == $id)), options: {instructions: "explain control edit"}}' \
  > var/copy/suggest.json
humanus suggest --request var/copy/suggest.json
```

The options respect the policy pack's guidance (tone, evidence rules, the word table). A person picks
one, or none, against `editorial-rewrite-skill.yml`.

Most of the copy is not in a page file: it is in `biased_decisions/leaderboard.py` and `compliance.py`
(the descriptions, the risk panels, the guidance), in `site/src/pages/*.astro`, and in
`site/src/lib/*.js` (the sentences the site builds from the data). Rewrite it there, rebuild, scan again.

## The two checks, and what each is for

- **`plain-language.test.mjs`** is exact and cheap: it fails on the words in the word table, on every
  built page, including alt text and previews. It is part of `npm test`, so the build fails if jargon returns.
- **Humanus** reads for what a word list cannot: a sentence that is hard to follow, a term that is
  never defined, a claim with nothing behind it, the same phrase repeated down a page.

Neither replaces reading the page as the person it is written for.
