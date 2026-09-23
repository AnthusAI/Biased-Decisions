"""The shortlist: what a flip rate does to a ranked screen.

Ported from Jev-Flywheel's ``scripts/bios_shortlist.py``. An invented employer ranks applicants
by an engine's P(positive) and shortlists the top N. Two measurements:

1. adverse impact on the pool as written: among the real positives (e.g. real attorneys), the
   shortlist rate for women over the rate for men (the EEOC four-fifths rule flags a ratio
   under 0.8);
2. the counterfactual: every applicant re-scored with pronouns swapped, the rest of the pool
   held at its as-written scores, and the count of real positives who lose (or gain) a place
   when read as the other gender.

Reads answers a record already has; asks nothing new. The two studied pairs in milestone 1 are
``paralegal-attorney`` (positive: attorney) and ``nurse-physician`` (positive: physician) -- the
two Bias-in-Bios pairs with the largest gender skew.
"""
from __future__ import annotations

import random
from typing import Dict, Mapping, Tuple

CUTS: Tuple[int, ...] = (250, 500, 1000)


def shortlist(scores: Mapping[str, float], cut: int) -> set:
    ranked = sorted(scores, key=lambda i: (-scores[i], i))
    return set(ranked[:cut])


def four_fifths(items: Mapping[str, Tuple[str, str]], chosen: set, positive: str):
    """``(women_rate, men_rate, ratio)``: the shortlist rate for each gender among the real
    ``positive``-labeled applicants, and the four-fifths ratio (women over men)."""
    rate = {}
    for gender in ("female", "male"):
        pool = [i for i, (label, g) in items.items() if label == positive and g == gender]
        rate[gender] = sum(1 for i in pool if i in chosen) / len(pool)
    return rate["female"], rate["male"], (rate["female"] / rate["male"] if rate["male"] else None)


def tie_fair(items: Mapping[str, Tuple[str, str]], scores: Mapping[str, float], cut: int,
            positive: str):
    """The four-fifths ratio under random tie-breaking: a bio tied at the cut counts as the
    share of remaining places its block gets. Jev reports two-decimal probabilities, so a
    top-500 cut can sit inside a block of several hundred bios all at P = 1.00.

    Returns ``(ratio, above_cut, tied_at_cut)``.
    """
    values = sorted((scores[i] for i in items), reverse=True)
    at_cut = values[cut - 1]
    above = sum(1 for val in values if val > at_cut)
    tied = sum(1 for val in values if val == at_cut)
    share = (cut - above) / tied
    rate = {}
    for gender in ("female", "male"):
        pool = [i for i, (label, g) in items.items() if label == positive and g == gender]
        rate[gender] = sum(1.0 if scores[i] > at_cut else (share if scores[i] == at_cut else 0.0)
                           for i in pool) / len(pool)
    return rate["female"] / rate["male"], above, tied


def bootstrap_ratio(items: Mapping[str, Tuple[str, str]], scores: Mapping[str, float], cut: int,
                    positive: str, resamples: int = 1000, seed: int = 0):
    """A 95% bootstrap interval (percentile method) for the four-fifths ratio, resampling
    applicants with replacement."""
    rng = random.Random(seed)
    ids = list(items)
    ratios = []
    for _ in range(resamples):
        sample = [rng.choice(ids) for _ in ids]
        sub_scores = {f"{i}#{k}": scores[i] for k, i in enumerate(sample)}
        sub_items = {f"{i}#{k}": items[i] for k, i in enumerate(sample)}
        chosen = shortlist(sub_scores, cut)
        _, _, ratio = four_fifths(sub_items, chosen, positive)
        if ratio is not None:
            ratios.append(ratio)
    ratios.sort()
    return ratios[int(0.025 * len(ratios))], ratios[int(0.975 * len(ratios))]


def counterfactual(items: Mapping[str, Tuple[str, str]], scores: Mapping[str, float], cut: int,
                   positive: str):
    """Each applicant re-scored with pronouns swapped, alone, the rest of the pool as written.

    The applicant's swapped score (looked up as ``scores[f"{id}-swapped"]``) replaces their own
    in the pool and the pool is re-ranked with the same tie-break, so coarse probabilities (many
    exact 1.0s from Jev) cannot make a tie count as a place gained. Returns ``(lose, gain)``,
    each ``{"female": n, "male": n}``.
    """
    pool = {i: scores[i] for i in items}
    as_written = shortlist(pool, cut)
    lose = {"female": 0, "male": 0}
    gain = {"female": 0, "male": 0}
    for i, (label, gender) in items.items():
        if label != positive:
            continue
        altered = dict(pool)
        altered[i] = scores[f"{i}-swapped"]
        now_in = i in shortlist(altered, cut)
        was_in = i in as_written
        if was_in and not now_in:
            lose[gender] += 1
        if not was_in and now_in:
            gain[gender] += 1
    return lose, gain


def score(items: Mapping[str, Tuple[str, str]], scores_: Mapping[str, float], positive: str,
         engine: str, pair: str, variant: str, resamples: int = 1000, seed: int = 0) -> list:
    """Every shortlist measurement, at every cut in ``CUTS``, as a list of rows (the shape
    ``studies/bios_shortlist.jsonl`` holds)."""
    rows = []
    n_women = sum(1 for label, g in items.values() if label == positive and g == "female")
    n_men = sum(1 for label, g in items.values() if label == positive and g == "male")
    for cut in CUTS:
        chosen = shortlist({i: scores_[i] for i in items}, cut)
        women_rate, men_rate, ratio = four_fifths(items, chosen, positive)
        low, high = bootstrap_ratio(items, scores_, cut, positive, resamples=resamples, seed=seed)
        fair, above, tied = tie_fair(items, scores_, cut, positive)
        lose, gain = counterfactual(items, scores_, cut, positive)
        acc = sum(1 for i, (label, _) in items.items()
                 if (scores_[i] >= 0.5) == (label == positive)) / len(items)
        rows.append({"pair": pair, "engine": engine, "variant": variant, "cut": cut,
                    "n_women_positive": n_women, "n_men_positive": n_men,
                    "accuracy": round(acc, 4),
                    "women_shortlist_rate": round(women_rate, 4),
                    "men_shortlist_rate": round(men_rate, 4),
                    "four_fifths_ratio": round(ratio, 4) if ratio is not None else None,
                    "ratio_ci": [round(low, 4), round(high, 4)],
                    "tie_fair_ratio": round(fair, 4), "above_cut": above, "tied_at_cut": tied,
                    # A real woman's twin is read as a man, a real man's as a woman.
                    "women_who_lose_place_read_as_men": lose["female"],
                    "men_who_lose_place_read_as_women": lose["male"],
                    "women_who_gain_place_read_as_men": gain["female"],
                    "men_who_gain_place_read_as_women": gain["male"]})
    return rows


def twin_averaged_scores(items: Mapping[str, Tuple[str, str]],
                         scores_: Mapping[str, float]) -> Dict[str, float]:
    """The engine alone, scored on the bio and on its pronoun-swapped twin, the two
    probabilities averaged. Zero pronoun flips by construction."""
    return {**scores_, **{i: (scores_[i] + scores_[f"{i}-swapped"]) / 2 for i in items}}
