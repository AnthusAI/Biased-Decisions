"""Bootstrap confidence intervals: the percentile method, over bios, seed fixed.

Every study in this package resamples the same way -- ``random.Random(0)``, 1,000 resamples
(unless a caller passes fewer for a faster test), percentile method -- so replaying a committed
row with the same seed and resample count reproduces its interval exactly, not just within
noise. Ported from the identical bootstrap routines duplicated across Jev-Flywheel's
``scripts/bios_pairs.py``, ``scripts/bios_race.py``, ``scripts/bios_race2.py`` and
``scripts/bios_age.py`` -- here they are one implementation each, called from every study that
needs them.
"""
from __future__ import annotations

import random
from typing import Callable, List, Mapping, Sequence, Tuple, TypeVar

V = TypeVar("V")


def paired(a: Sequence[V], b: Mapping[str, V]) -> List[Tuple[V, V]]:
    """(a, b) pairs, over items that have both, matched by ``item_id``. Order follows ``a``.

    Every verdict-like object this package resamples (``biased_decisions.metrics.flips.Verdict``
    and friends) has an ``item_id`` field; this only reads that attribute, so it works for any of
    them without a per-study copy.
    """
    return [(v, b[v.item_id]) for v in a if v.item_id in b]


def bootstrap_flip_ci(a: Sequence[V], b: Mapping[str, V], *,
                      resamples: int = 1000, seed: int = 0) -> Tuple[float, float]:
    """A 95% bootstrap interval (percentile method) for the flip rate between ``a`` and ``b``,
    resampling bios with replacement. ``(0.0, 0.0)`` if there is nothing to pair.

    Ported from Jev-Flywheel's ``scripts/bios_pairs.bootstrap_flip_ci`` and
    ``scripts/bios_race.bootstrap_flip_ci``, which were byte-identical.
    """
    pairs = paired(a, b)
    n = len(pairs)
    if n == 0:
        return (0.0, 0.0)
    rng = random.Random(seed)
    stats = []
    for _ in range(resamples):
        flips = 0
        for _i in range(n):
            av, bv = pairs[rng.randrange(n)]
            if av.predicted != bv.predicted:
                flips += 1
        stats.append(flips / n)
    stats.sort()
    lo_i = int(0.025 * resamples)
    hi_i = min(int(0.975 * resamples), resamples - 1)
    return (round(stats[lo_i], 4), round(stats[hi_i], 4))


def bootstrap_ci(a: Sequence[V], b: Mapping[str, V], stat: Callable[[Sequence[Tuple[V, V]]], float],
                 *, resamples: int = 1000, seed: int = 0) -> Tuple[float, float]:
    """A 95% bootstrap interval (percentile method) for an arbitrary ``stat`` computed over
    (a, b) pairs, resampling bios with replacement. ``(0.0, 0.0)`` if there is nothing to pair.

    Ported from Jev-Flywheel's ``scripts/bios_age.bootstrap_ci``.
    """
    pairs = paired(a, b)
    n = len(pairs)
    if n == 0:
        return (0.0, 0.0)
    rng = random.Random(seed)
    stats = []
    for _ in range(resamples):
        resampled = [pairs[rng.randrange(n)] for _ in range(n)]
        stats.append(stat(resampled))
    stats.sort()
    lo_i = int(0.025 * resamples)
    hi_i = min(int(0.975 * resamples), resamples - 1)
    return (round(stats[lo_i], 4), round(stats[hi_i], 4))


def bootstrap_mean_ci(values: Sequence[float], *, resamples: int = 1000,
                      seed: int = 0) -> Tuple[float, float]:
    """A 95% bootstrap interval (percentile method) for the mean of ``values``, resampling with
    replacement. ``(0.0, 0.0)`` if there is nothing to resample.

    Ported from Jev-Flywheel's ``scripts/bios_race2.bootstrap_mean_ci``.
    """
    n = len(values)
    if n == 0:
        return (0.0, 0.0)
    rng = random.Random(seed)
    stats = []
    for _ in range(resamples):
        total = 0.0
        for _i in range(n):
            total += values[rng.randrange(n)]
        stats.append(total / n)
    stats.sort()
    lo_i = int(0.025 * resamples)
    hi_i = min(int(0.975 * resamples), resamples - 1)
    return (round(stats[lo_i], 4), round(stats[hi_i], 4))
