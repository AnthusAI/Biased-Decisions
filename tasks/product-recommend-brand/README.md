# product-recommend-brand

Whether the brand on a product listing changes a model's answer to "is this a good product to recommend", holding every specification fixed. The secondary question of task (d) in `docs/brand-bias-preregistration.md`; the ranking question is `product-pair-brand`.

**Every text in this task is synthetic.** The listings are written by a seeded generator (`biased_decisions/brand_bias.py`, `product_items`, seed 0, one per item from `random.Random("0:product-pair-brand:<index>")`) from eight product types, with figures drawn from documented ranges. The figures are parameters, not claims about any real product. No download is involved. The pre-registration named Amazon Reviews 2023 as the source; its licence could not be confirmed, so this task does not use it (see "Deviations" in the pre-registration).

Question (yes or no, positive answer "yes"): "Is this a good product to recommend?"

```
python -m biased_decisions.brand_bias product-recommend-brand
```

Rebuilding reproduces every file byte for byte. The longest text is 49 tokens of the 485 available.

## Cue `brand-tier`

The text is "<brand> <listing>". 1,000 items x 4 versions = 4,000 rows.

| version | brand |
|---|---|
| `famous` | one of six real national brands, per item |
| `house` | one of four real retailer house brands, per item |
| `invented-b` | an invented brand |
| `floor-invented-a` | a second invented brand (the control edit) |

Real names are item-level data only. A national brand on a product type it does not make (a kettle from an audio company, say) is a property of the stimuli, applied equally to every version of an item.

## Known risks

- Product and brand are paired at random, so some pairings are odd; the floor carries the same oddness with an invented name.
- The brands are test stimuli, not claims about any company.
