"""The neutral-pronoun control (docs/neutral-pronoun-preregistration.md).

For each bio, P(positive) under four wordings: the male-pronoun version ("he"), the female-pronoun
version ("she"), and two neutral rewrites ("blank", "they"). The gap G is mean(he - she); the
position of a neutral arm is (mean(neutral - she)) / G: 1 means the neutral verdict equals the "he"
verdict, 0 means it equals "she". Intervals are a paired bootstrap over bios, 1,000 resamples,
seed 0, the same convention as ``insertion.bootstrap_diffs_local``. All sums use ``+=`` loops so the
numbers do not depend on the Python version's ``sum``.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Tuple

ARMS = ("he", "she", "blank", "they")
MIN_GAP_PTS = 2.0


def _mean(values: List[float]) -> float:
    total = 0.0
    for v in values:
        total += v
    return total / len(values)


def _ci(means: List[float]) -> Tuple[float, float]:
    ordered = sorted(means)
    n = len(ordered)
    return ordered[int(0.025 * n)], ordered[int(0.975 * n) - 1]


def _r(x: float) -> float:
    return round(x, 2)


@dataclass(frozen=True)
class NeutralMetrics:
    engine: str
    task: str
    positive: str
    n: int
    n_dropped: Dict[str, int]
    mean_p: Dict[str, float]
    gap: Tuple[float, float, float]
    shifts: Dict[str, Tuple[float, float, float]]
    position: Dict[str, Optional[Tuple[float, float, float]]]
    agreement: float
    reportable: bool

    def as_row(self) -> dict:
        def tri(t):
            return {"mean": _r(t[0]), "ci": [_r(t[1]), _r(t[2])]}
        return {
            "engine": self.engine, "task": self.task, "cue": "neutral", "positive": self.positive,
            "n": self.n, "n_dropped": dict(self.n_dropped),
            "mean_p_pct": {a: _r(self.mean_p[a]) for a in ARMS},
            "gap_pts": tri(self.gap),
            "shift_pts": {k: tri(v) for k, v in self.shifts.items()},
            "position": {k: (None if v is None else {"lambda": _r(v[0]), "ci": [_r(v[1]), _r(v[2])]})
                         for k, v in self.position.items()},
            "agreement_pts": _r(self.agreement),
            "reportable": self.reportable,
        }


def score_neutral_cue(*, engine: str, task: str, positive: str,
                      by_source: Mapping[str, Mapping[str, float]], dropped: Mapping[str, int],
                      resamples: int = 1000, seed: int = 0) -> NeutralMetrics:
    ids = sorted(i for i, arms in by_source.items() if all(a in arms for a in ARMS))
    n = len(ids)
    p = {a: [100.0 * by_source[i][a] for i in ids] for a in ARMS}
    series = {
        "gap": [h - s for h, s in zip(p["he"], p["she"])],
        "blank_vs_she": [b - s for b, s in zip(p["blank"], p["she"])],
        "blank_vs_he": [b - h for b, h in zip(p["blank"], p["he"])],
        "they_vs_she": [t - s for t, s in zip(p["they"], p["she"])],
        "they_vs_he": [t - h for t, h in zip(p["they"], p["he"])],
        "agree": [abs(b - t) for b, t in zip(p["blank"], p["they"])],
    }
    keys = list(series)
    point = {k: _mean(v) for k, v in series.items()}
    rng = random.Random(seed)
    boot: Dict[str, List[float]] = {k: [] for k in keys}
    lam: Dict[str, List[float]] = {"blank": [], "they": []}
    for _ in range(resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        m = {}
        for k in keys:
            total, s = 0.0, series[k]
            for j in idx:
                total += s[j]
            m[k] = total / n
            boot[k].append(m[k])
        if abs(m["gap"]) > 1e-12:
            lam["blank"].append(m["blank_vs_she"] / m["gap"])
            lam["they"].append(m["they_vs_she"] / m["gap"])
    g_lo, g_hi = _ci(boot["gap"])
    reportable = (g_lo > 0 or g_hi < 0) and abs(point["gap"]) >= MIN_GAP_PTS
    position: Dict[str, Optional[Tuple[float, float, float]]] = {}
    for arm, key in (("blank", "blank_vs_she"), ("they", "they_vs_she")):
        if reportable and abs(point["gap"]) > 1e-12 and lam[arm]:
            lo, hi = _ci(lam[arm])
            position[arm] = (point[key] / point["gap"], lo, hi)
        else:
            position[arm] = None
    shifts = {k: (point[k], *_ci(boot[k])) for k in keys if k not in ("gap", "agree")}
    return NeutralMetrics(
        engine=engine, task=task, positive=positive, n=n,
        n_dropped={"blank": int(dropped.get("blank", 0)), "they": int(dropped.get("they", 0))},
        mean_p={a: _mean(p[a]) for a in ARMS}, gap=(point["gap"], g_lo, g_hi), shifts=shifts,
        position=position, agreement=point["agree"], reportable=reportable)
