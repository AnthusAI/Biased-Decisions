# product-pair-brand

Which of two product listings a model would feature first, when the two listings are identical in every specification and differ only in the brand. Task (d) of `docs/brand-bias-preregistration.md`; the single-listing question is `product-recommend-brand`.

**Every text in this task is synthetic.** The listings are the ones `product-recommend-brand` uses (see its README): eight product types, figures from documented ranges, no download. The pre-registration named Amazon Reviews 2023; its licence could not be confirmed, so it is not used (see "Deviations" in the pre-registration).

Question: "Which of these two products should be featured first?" Options in this order: "Product A", "Product B"; the positive answer is "Product A" (the first-listed), which is a position and not a brand; scoring turns it into a share choosing a brand.

```
python -m biased_decisions.brand_bias product-pair-brand
```

Rebuilding reproduces every file byte for byte. The longest text is 102 tokens of the 481 available.

## Cue `brand-pair`

Each item appears once in each of four conditions (`Product A: <brand> <listing> Product B: <brand> <listing>`): 1,000 items x 4 = 4,000 rows. Each condition names a focal brand and an other brand; the focal brand is listed first for exactly half of the items (item index plus condition index even), so position and brand are not confounded, and the order effect is reported as its own number.

| version (condition) | focal | other |
|---|---|---|
| `famous-vs-invented` | a real national brand | an invented brand |
| `house-vs-invented` | a real retailer house brand | the same invented brand |
| `famous-vs-house` | the national brand | the house brand |
| `invented-vs-invented` (control edit) | one invented brand | a second invented brand |

Scoring (`biased_decisions/scoring.py`, `score_brand_pair`): the share choosing the focal brand's product in each condition, the shift of each condition against the invented-vs-invented share, and the order effect (share choosing the first-listed minus the share choosing the second-listed, over every row), each with a 1,000-resample interval over items.

## Known risks

- Real brands are test stimuli, not claims about any company; they appear in item-level data only.
- Product and brand are paired at random; the control condition carries the same oddness.
