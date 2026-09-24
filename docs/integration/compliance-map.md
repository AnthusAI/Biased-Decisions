# Integration note: the compliance map for the newer decisions

Package `compliance-map`. Data lives in `biased_decisions/compliance.py`; every quoted passage is
in `docs/legal-sources.md` with its URL and fetch date (2026-09-23).

## What was added

| decision (board) | rules cited | status |
|---|---|---|
| Opioid prescribing, gender / race / disability | ACA Section 1557 (42 U.S.C. 18116), 45 CFR 92.210 | mapped, practice `healthcare` |
| Comment removal, sexuality / race / disability / religion | EU Digital Services Act Art. 14(4), Arts. 20 and 21 | mapped, practice `moderation`; `us_note` says U.S. law leaves this to platform policy and cites no U.S. rule |
| Hiring, sexuality (when those tests exist) | Title VII as read in Bostock v. Clayton County, 590 U.S. 644 (2020); EU AI Act Annex III 4(a) | mapped, per decision |
| Hiring, veteran status (when those tests exist) | USERRA, 38 U.S.C. 4311(a) | mapped, per decision |
| Opioid prescribing, veteran status | none | stays "not yet mapped", with the reason: no verified rule governs veteran status in a prescribing decision (USERRA is employment law) |
| Credit (`pending`) | ECOA 15 U.S.C. 1691(a), Regulation B 12 CFR 1002.4(a) and 1002.2(z), EU AI Act Annex III 5(b) | listed only; marital status carried by ECOA and Reg B |
| Housing (`pending`) | Fair Housing Act 42 U.S.C. 3604(a) and (b), 3602(k) | listed only; familial status carried by 3604 and 3602(k) |

`eu-ai-act-5` (Annex III point 5(a), (b), (c)) is cited only for credit. Point 5(a) covers health
care only when a public authority decides eligibility for benefits, and 5(c) covers life and
health insurance, so neither is a fit for a prescribing decision and neither is cited for it.

The credit and housing rows are in a new top-level `pending` list, not in `mapping`, because
`mapping` has exactly one row per public characteristic and marital and familial status are not
characteristic boards yet. A `pending` entry never produces a warning.

## The data shape (implemented, backward compatible)

Each `mapping` row keeps every field it had. A row may now also carry:

```json
"decisions": [
  {"items": ["qpain-treatment"], "regulated": true, "practice": "healthcare", "attribute": "sex",
   "decision": "...", "citations": ["aca-1557", "hhs-92-210"], "failure_mode": "...",
   "who_harmed": "...", "recipes": ["..."], "insights": ["..."]}
]
```

`items` are task ids as they appear in the board's cells (`cell.item`). A decision entry has the
same fields and the same bar as a row (verified citations, recipes and insights that exist,
`reason` when not regulated), and a moderation entry adds `us_note`. An item is claimed by at most
one entry on a board. A row with no `decisions` field answers for every item, as before.
`compliance.mapping_for(mapping, dimension, item)` returns the entry for an item, else the row.

The row itself stays the default for the board's measured decisions that no `decisions` entry
names: for gender, race, age, disability and religion that is hiring; for sexuality that is
comment removal (the only sexuality data today); veteran stays unregulated because its only
data is opioid prescribing.

## What the site would change (not implemented)

1. `site/src/lib/compliance.js`
   - `mappingOf(dimId)` becomes `mappingOf(dimId, itemId)` and calls the same rule as
     `mapping_for`: the `decisions` entry whose `items` contain `itemId`, else the row.
   - `isRegulated(dimId, itemId)`, `warnLabel(dimId, itemId)` take the item and read the
     practice from that entry. `regulatedDims` stays for the home page flags.
2. `site/src/lib/site.js`: delete `NON_HIRING_ITEMS` and `isNonHiring`; the mapping now says which
   decisions are regulated.
3. Pages: `pages/[dim]/[a]/index.astro` drops the `!isNonHiring(level)` guards and passes
   `level.item` to `RegWarn` and `RiskPanel`; `RegWarn.astro`, `RiskPanel.astro`, `Board.astro`
   and `EvidenceItem.astro` read the entry returned for the item (its practice label, citations,
   `failure_mode`, `who_harmed`, `recipes`, `insights`, and `us_note` when present, shown once
   under the citations). The board-level page (`/sexuality/`) shows the row's warning only when
   every item on the board resolves to a regulated entry; otherwise it links to each decision's
   warning.
4. `site/test/compliance.test.mjs`: `dimOfPath` stops excluding the opioid and comment paths;
   the tests resolve the entry per (board, item) instead.
5. `site/data/leaderboard.json` must be regenerated (`make leaderboard`) after the site change.
   It was not regenerated here, so today's site is unchanged.

Plain-language labels for the new practices: "Treatment decisions in health care", "Removing
online comments", "Lending decisions", "Housing decisions".
