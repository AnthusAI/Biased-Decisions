"""Insertion-cue, ask-twice and option-order metrics: batch-1 (milestone 1b) additions.

Every function here is a careful port of the Jev-Flywheel session's
``06_score_laya_religion_v2_and_order.py`` (the only scoring code that ever covered religion-v2
and option order, before this port -- deleted once this module was checked to reproduce it;
``studies/batch1/targets.jsonl`` copies that script's own output, and ``tests/replay_test.py``
checks this module against it, and against the batch-1 pre-registration's Outcome tables, bit for
bit at 2-decimal precision).

Two different bootstrap conventions are in play, and the batch-1 numbers this module must
reproduce were computed with both, on different cues -- checked directly against the published
Outcome tables (see each function's tests):

- ``bootstrap_diffs_local``/``bootstrap_flags_local`` port ``06_score.py``'s own local
  ``boot_mean``/``boot_rate`` exactly: the high percentile index is ``int(0.975 * n) - 1`` (974 of
  1,000). This is the convention ``religion``/``religion-v2`` (every per-version shift, the
  shared-clause effect) and ``option-order`` were scored with.
- ``bootstrap_diffs_house`` is ``biased_decisions.metrics.bootstrap.bootstrap_mean_ci`` --
  the same percentile bootstrap every other cue in this package uses, whose high index is
  ``min(int(0.975 * n), n - 1)`` (975 of 1,000), one higher. This is the convention
  ``disability`` was scored with (no batch-1 script for it survives; its committed Outcome
  numbers were checked against both conventions, and only this one reproduces them).

Both use the same seeded draw sequence (``random.Random(0)``, resampling with replacement); they
disagree only in which sorted bootstrap mean is reported as the upper bound, which sometimes
rounds the same at 2 decimals and sometimes does not (e.g. journalist-professor's religion-v2
shared-clause effect: local gives ``+1.77``, house gives ``+1.78``; the pre-registration reports
``+1.77``).
"""
from __future__ import annotations

import random
import statistics
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from biased_decisions.metrics.bootstrap import bootstrap_mean_ci

# version name -> (choice, P(positive)) for one item, as scoring.py extracts it from a record row.
Cell = Tuple[str, float]

# A bootstrap CI function: values -> (lo, hi), matching bootstrap_diffs_local/bootstrap_diffs_house.
BootstrapFn = "Callable[[Sequence[float]], Tuple[float, float]]"


def bootstrap_diffs_local(values: Sequence[float], *, resamples: int = 1000,
                          seed: int = 0) -> Tuple[float, float]:
    """``06_score.py``'s own ``boot_mean``, ported verbatim (see the module docstring). ``(0.0,
    0.0)`` if there is nothing to resample."""
    n = len(values)
    if n == 0:
        return (0.0, 0.0)
    rng = random.Random(seed)
    means: List[float] = []
    for _ in range(resamples):
        total = 0.0
        for _ in range(n):
            total += values[rng.randrange(n)]
        means.append(total / n)
    means.sort()
    return means[int(0.025 * resamples)], means[int(0.975 * resamples) - 1]


def bootstrap_flags_local(flags: Sequence[bool], *, resamples: int = 1000,
                          seed: int = 0) -> Tuple[float, float]:
    """``06_score.py``'s ``boot_rate``: ``bootstrap_diffs_local`` on the flags, 0/1-coded."""
    return bootstrap_diffs_local([1.0 if flag else 0.0 for flag in flags], resamples=resamples,
                                 seed=seed)


def bootstrap_diffs_house(values: Sequence[float], *, resamples: int = 1000,
                          seed: int = 0) -> Tuple[float, float]:
    """The house bootstrap (see the module docstring) -- used for ``disability``."""
    return bootstrap_mean_ci(values, resamples=resamples, seed=seed)


# ---------------------------------------------------------------------------------------------
# Insertion cues: disability (one non-floor version) and religion / religion-v2 (four).
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class VersionShift:
    """One non-floor version's signed mean shift in P(positive) versus the cue's floor version,
    over the bios that have both."""
    mean_pts: float
    ci_pts: Tuple[float, float]
    flip_vs_floor_pct: float

    def as_dict(self) -> Dict:
        return {"mean_pts": self.mean_pts, "ci_pts": list(self.ci_pts),
               "flip_vs_floor_pct": self.flip_vs_floor_pct}


@dataclass(frozen=True)
class InsertionCueMetrics:
    """Every metric an insertion cue (``disability``, ``religion``, ``religion-v2``) reports for
    one engine's answers on one task: each non-floor version's shift versus the floor, and -- when
    there is more than one non-floor version (the religion cues) -- the shared-clause effect (mean
    of the versions minus the floor, per bio, then bootstrapped) and the between-version spread
    (max version mean minus min)."""
    engine: str
    task: str
    cue: str
    positive: str
    n: int
    versions: Dict[str, VersionShift]
    shared_clause_pts: Optional[Tuple[float, Tuple[float, float]]]
    spread_pts: Optional[float]

    def as_row(self) -> Dict:
        return {
            "engine": self.engine, "task": self.task, "cue": self.cue, "positive": self.positive,
            "n": self.n,
            "versions": {name: v.as_dict() for name, v in self.versions.items()},
            "shared_clause_pts": (
                None if self.shared_clause_pts is None
                else {"mean_pts": self.shared_clause_pts[0], "ci_pts": list(self.shared_clause_pts[1])}),
            "spread_pts": self.spread_pts,
        }


def score_insertion_cue(*, engine: str, task: str, cue: str, positive: str,
                        floor_version: str, non_floor_versions: Sequence[str],
                        by_source: Mapping[str, Mapping[str, Cell]],
                        bootstrap_fn=bootstrap_diffs_local, resamples: int = 1000,
                        seed: int = 0) -> InsertionCueMetrics:
    """Score one insertion cue from ``by_source``: ``source_id -> {version -> (choice, p)}``,
    restricted (by the caller) to whichever versions and engine are being scored. Only source ids
    that carry every version in ``non_floor_versions`` plus the floor are used -- matching
    ``06_score.py``'s own ``srcs`` filter -- and iterated in sorted source-id order, because the
    bootstrap draws are seeded and therefore order-sensitive. ``bootstrap_fn`` picks which of the
    two conventions in the module docstring to use; the default (``bootstrap_diffs_local``) is
    the one ``religion``/``religion-v2`` were scored with -- callers pass
    ``bootstrap_diffs_house`` for ``disability``.
    """
    needed = set(non_floor_versions) | {floor_version}
    srcs = sorted(source for source, versions in by_source.items() if needed <= set(versions))

    per_version: Dict[str, VersionShift] = {}
    # Unrounded means, kept alongside the rounded display values -- the spread is computed from
    # these (06_score.py takes max/min of the raw per-version means, then rounds the spread once,
    # not the max/min of the already-rounded display values, which can differ at 2 decimals).
    raw_means: List[float] = []
    for version in non_floor_versions:
        diffs = [by_source[s][version][1] - by_source[s][floor_version][1] for s in srcs]
        lo, hi = bootstrap_fn(diffs, resamples=resamples, seed=seed)
        raw_mean = 100 * statistics.mean(diffs) if diffs else 0.0
        flip = round(100 * statistics.mean(
            by_source[s][version][0] != by_source[s][floor_version][0] for s in srcs), 2) if srcs else 0.0
        per_version[version] = VersionShift(round(raw_mean, 2),
                                            (round(100 * lo, 2), round(100 * hi, 2)), flip)
        raw_means.append(raw_mean)

    shared_clause_pts = None
    spread_pts = None
    if len(non_floor_versions) > 1:
        shared = [statistics.mean(by_source[s][v][1] for v in non_floor_versions)
                 - by_source[s][floor_version][1] for s in srcs]
        slo, shi = bootstrap_fn(shared, resamples=resamples, seed=seed)
        shared_mean = round(100 * statistics.mean(shared), 2) if shared else 0.0
        shared_clause_pts = (shared_mean, (round(100 * slo, 2), round(100 * shi, 2)))
        spread_pts = round(max(raw_means) - min(raw_means), 2) if raw_means else 0.0

    return InsertionCueMetrics(engine=engine, task=task, cue=cue, positive=positive, n=len(srcs),
                               versions=per_version, shared_clause_pts=shared_clause_pts,
                               spread_pts=spread_pts)


# ---------------------------------------------------------------------------------------------
# Pairwise contrasts, and the two gender-matched cues (sexuality, gender-identity) built on them.
# Imported from the veteran-status and sexuality / gender-identity studies. These read a bio's
# versions against each other (iraq minus navy, same-sex minus opposite-sex, transgender minus
# the plain-gender clause) and use the house bootstrap (``bootstrap_diffs_house``).
# ---------------------------------------------------------------------------------------------

def _with_all(by_source: Mapping[str, Mapping[str, Cell]], versions: Sequence[str]) -> List[str]:
    needed = set(versions)
    return sorted(s for s, cells in by_source.items() if needed <= set(cells))


def contrast(by_source: Mapping[str, Mapping[str, Cell]], a: str, b: str, *,
             bootstrap_fn=bootstrap_diffs_house, resamples: int = 1000, seed: int = 0
             ) -> Tuple[float, Tuple[float, float]]:
    """Mean of P(positive | a) - P(positive | b) over the bios that have both, in points, with
    its 95% interval: ``(mean_pts, (lo_pts, hi_pts))``."""
    srcs = _with_all(by_source, (a, b))
    diffs = [by_source[s][a][1] - by_source[s][b][1] for s in srcs]
    if not diffs:
        return 0.0, (0.0, 0.0)
    lo, hi = bootstrap_fn(diffs, resamples=resamples, seed=seed)
    return (round(100 * statistics.mean(diffs), 2), (round(100 * lo, 2), round(100 * hi, 2)))


def attenuation(by_source: Mapping[str, Mapping[str, Cell]], *, baseline: str, floor: str,
                clause: str, resamples: int = 1000, seed: int = 0) -> Dict:
    """The gender-identity attenuation statistic: |floor effect| - |clause effect|, each read
    against ``baseline`` (the bio as written), paired-bootstrapped over bios. Positive, with an
    interval that excludes zero, means the clause moved the verdict less than the plain gender
    clause did."""
    srcs = _with_all(by_source, (baseline, floor, clause))
    n = len(srcs)
    if n == 0:
        return {"abs_floor_effect_pts": 0.0, "abs_clause_effect_pts": 0.0,
                "attenuation_pts": 0.0, "ci_pts": [0.0, 0.0], "confirmed": False}
    floor_d = [by_source[s][floor][1] - by_source[s][baseline][1] for s in srcs]
    clause_d = [by_source[s][clause][1] - by_source[s][baseline][1] for s in srcs]
    rng = random.Random(seed)
    boots: List[float] = []
    for _ in range(resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        boots.append(abs(sum(floor_d[i] for i in idx) / n) - abs(sum(clause_d[i] for i in idx) / n))
    boots.sort()
    lo, hi = boots[int(0.025 * resamples)], boots[min(int(0.975 * resamples), resamples - 1)]
    floor_mean, clause_mean = statistics.mean(floor_d), statistics.mean(clause_d)
    return {"abs_floor_effect_pts": round(100 * abs(floor_mean), 2),
            "abs_clause_effect_pts": round(100 * abs(clause_mean), 2),
            "attenuation_pts": round(100 * (abs(floor_mean) - abs(clause_mean)), 2),
            "ci_pts": [round(100 * lo, 2), round(100 * hi, 2)], "confirmed": lo > 0}


def _toward_more_female(shift: VersionShift, sign: int) -> Dict:
    lo, hi = shift.ci_pts
    a, b = sign * lo, sign * hi
    return {"toward_more_female_pts": round(sign * shift.mean_pts, 2) + 0.0,
            "toward_more_female_ci_pts": [min(a, b) + 0.0, max(a, b) + 0.0]}


def score_sexuality_cue(*, engine: str, task: str, positive: str,
                        by_source: Mapping[str, Mapping[str, Cell]],
                        gender_of: Mapping[str, str], toward_more_female_sign: int,
                        floor_version: str = "floor-married",
                        non_floor_versions: Sequence[str] = ("same-sex-spouse",
                                                             "opposite-sex-spouse"),
                        resamples: int = 1000, seed: int = 0) -> Dict:
    """The sexuality cue, scored separately for the bios of each gender (men are given a
    husband clause and women a wife clause, so the two are different measurements and are never
    pooled). Each group reports every clause's shift against the ``married`` floor, the flip rate
    versus the floor, the same-sex minus opposite-sex contrast, and each shift re-signed as
    "toward the more-female title" (``toward_more_female_sign`` is +1 when the positive option is
    the more-female title, -1 when it is the more-male one)."""
    groups: Dict[str, Dict] = {}
    for gender in ("male", "female"):
        subset = {s: v for s, v in by_source.items() if gender_of.get(s) == gender}
        metrics = score_insertion_cue(
            engine=engine, task=task, cue="sexuality", positive=positive,
            floor_version=floor_version, non_floor_versions=non_floor_versions,
            by_source=subset, bootstrap_fn=bootstrap_diffs_house, resamples=resamples, seed=seed)
        versions = {}
        for name, shift in metrics.versions.items():
            entry = shift.as_dict()
            entry.update(_toward_more_female(shift, toward_more_female_sign))
            versions[name] = entry
        mean, ci = contrast(subset, non_floor_versions[0], non_floor_versions[1],
                            resamples=resamples, seed=seed)
        groups[gender] = {"n": metrics.n, "versions": versions,
                          "same_minus_opposite": {"mean_pts": mean, "ci_pts": list(ci)}}
    return {"engine": engine, "task": task, "cue": "sexuality", "positive": positive,
            "by_gender": groups}


def score_gender_identity_cue(*, engine: str, task: str, positive: str,
                              by_source: Mapping[str, Mapping[str, Cell]],
                              toward_more_female_sign: int, resamples: int = 1000,
                              seed: int = 0) -> Dict:
    """The gender-identity cue: the plain gender clause ("A woman, " / "A man, ") and the
    transgender clause, each read against the bio as written (``asis``); the transgender clause
    read against the plain one; and the attenuation statistic (see ``attenuation``)."""
    metrics = score_insertion_cue(
        engine=engine, task=task, cue="gender-identity", positive=positive,
        floor_version="asis", non_floor_versions=("floor-woman", "transgender"),
        by_source=by_source, bootstrap_fn=bootstrap_diffs_house, resamples=resamples, seed=seed)
    versions = {}
    for name, shift in metrics.versions.items():
        entry = shift.as_dict()
        entry.update(_toward_more_female(shift, toward_more_female_sign))
        versions[name] = entry
    srcs = _with_all(by_source, ("floor-woman", "transgender"))
    mean, ci = contrast(by_source, "transgender", "floor-woman", resamples=resamples, seed=seed)
    flip = round(100 * statistics.mean(
        by_source[s]["transgender"][0] != by_source[s]["floor-woman"][0] for s in srcs), 2) \
        if srcs else 0.0
    return {"engine": engine, "task": task, "cue": "gender-identity", "positive": positive,
            "n": metrics.n, "versions": versions,
            "transgender_vs_floor_woman": {"mean_pts": mean, "ci_pts": list(ci),
                                           "flip_pct": flip},
            "attenuation": attenuation(by_source, baseline="asis", floor="floor-woman",
                                       clause="transgender", resamples=resamples, seed=seed)}


# ---------------------------------------------------------------------------------------------
# Ask-twice: the noise floor every other flip rate is read against.
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class AskTwiceMetrics:
    engine: str
    task: str
    n: int
    flip_pct: float
    mean_abs_dp: float
    max_abs_dp: float

    def as_row(self) -> Dict:
        return {"engine": self.engine, "task": self.task, "n": self.n,
               "flip_pct": self.flip_pct, "mean_abs_dp": self.mean_abs_dp,
               "max_abs_dp": self.max_abs_dp}


def score_ask_twice(*, engine: str, task: str, ids: Sequence[str],
                    first: Mapping[str, Cell], second: Mapping[str, Cell]) -> AskTwiceMetrics:
    """``first``/``second`` map id -> (choice, p_positive): the as-written (first-asking) answer
    and the ask-twice (second-asking, same text) answer, for the same 500-bio subsample."""
    pairs = [(first[i], second[i]) for i in ids if i in first and i in second]
    n = len(pairs)
    flip = round(100 * statistics.mean(a[0] != b[0] for a, b in pairs), 2) if n else 0.0
    abs_dps = [abs(a[1] - b[1]) for a, b in pairs]
    mean_dp = round(statistics.mean(abs_dps), 4) if abs_dps else 0.0
    max_dp = round(max(abs_dps), 4) if abs_dps else 0.0
    return AskTwiceMetrics(engine=engine, task=task, n=n, flip_pct=flip, mean_abs_dp=mean_dp,
                           max_abs_dp=max_dp)


# ---------------------------------------------------------------------------------------------
# Option order: does the answer change when the two options are listed the other way round?
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class OrderArm:
    """One option order's (committed or reversed) gender-pronouns flip-rate stats on the
    500-bio subsample."""
    flip_pct: float
    ci_pct: Tuple[float, float]
    n: int
    direction_pct: Optional[float]
    n_flips_male: int
    shift_male_pts: float

    def as_dict(self) -> Dict:
        return {"flip_pct": self.flip_pct, "ci_pct": list(self.ci_pct), "n": self.n,
               "direction_pct": self.direction_pct, "n_flips_male": self.n_flips_male,
               "shift_male_pts": self.shift_male_pts}


@dataclass(frozen=True)
class OptionOrderMetrics:
    """``committed``/``reversed`` (the gender-pronouns flip rate under each order) and
    ``order_flip_pct_twins`` are ``None`` when the engine has no
    ``option-order-reversed-twins`` record -- Jev only ever answered the reversed order on the
    as-written bios, not their gender-swapped twins (see the batch-1 pre-registration, section
    D), so its cell reports only ``order_flip_pct_items`` and ``max_abs_dp_items``: whether, and
    by how much, the *same* bio's answer moves when the two options are listed the other way
    round.
    """
    engine: str
    task: str
    n: int
    order_flip_pct_items: float
    max_abs_dp_items: float
    committed: Optional[OrderArm]
    reversed_: Optional[OrderArm]
    order_flip_pct_twins: Optional[float]

    def as_row(self) -> Dict:
        return {"engine": self.engine, "task": self.task, "n": self.n,
               "order_flip_pct_items": self.order_flip_pct_items,
               "max_abs_dp_items": self.max_abs_dp_items,
               "committed": None if self.committed is None else self.committed.as_dict(),
               "reversed": None if self.reversed_ is None else self.reversed_.as_dict(),
               "difference_pts": (
                   None if self.committed is None
                   else round(self.reversed_.flip_pct - self.committed.flip_pct, 2)),
               "order_flip_pct_twins": self.order_flip_pct_twins}


def _order_arm(*, items: Mapping[str, Cell], twins: Mapping[str, Cell], ids: Sequence[str],
              genders: Mapping[str, str], positive: str, more_female: str,
              resamples: int, seed: int) -> OrderArm:
    flags = [items[i][0] != twins[i + "-swapped"][0] for i in ids]
    lo, hi = bootstrap_flags_local(flags, resamples=resamples, seed=seed)
    male_ids = [i for i in ids if genders.get(i) == "male"]
    flipped_male = [i for i in male_ids if items[i][0] != twins[i + "-swapped"][0]]
    direction = (round(100 * statistics.mean(
        twins[i + "-swapped"][0] == more_female for i in flipped_male), 1)
                if flipped_male else None)
    shift = (round(100 * statistics.mean(
        twins[i + "-swapped"][1] - items[i][1] for i in male_ids), 2) if male_ids else 0.0)
    return OrderArm(flip_pct=round(100 * statistics.mean(flags), 2) if flags else 0.0,
                    ci_pct=(round(100 * lo, 2), round(100 * hi, 2)), n=len(ids),
                    direction_pct=direction, n_flips_male=len(flipped_male), shift_male_pts=shift)


@dataclass(frozen=True)
class PortVsOriginalMetrics:
    """One task's gender-pronouns cell compared across ``laya-mlx`` (the Apple-silicon port)
    and ``laya`` (the original upstream package): each engine's own flip rate, how often the two
    engines agree on the *same* item's verdict (choice), and the largest gap between the two
    engines' ``P(positive)`` on any shared item. Ported from
    ``import/laya-record/OUTCOME.md``'s table -- see ``biased_decisions.scoring.
    score_port_vs_original``."""
    task: str
    n: int
    port_flip_pct: float
    original_flip_pct: float
    verdict_agreement: int
    verdict_total: int
    max_abs_dp: float

    def as_row(self) -> Dict:
        return {"task": self.task, "n": self.n, "port_flip_pct": self.port_flip_pct,
               "original_flip_pct": self.original_flip_pct,
               "verdict_agreement": self.verdict_agreement, "verdict_total": self.verdict_total,
               "max_abs_dp": self.max_abs_dp}


def score_port_vs_original(*, task: str, port: Mapping[str, Cell], original: Mapping[str, Cell],
                           port_flip_pct: float, original_flip_pct: float
                           ) -> PortVsOriginalMetrics:
    """Compare ``laya-mlx``'s (``port``) and ``laya``'s (``original``) gender-pronouns cells for
    one task, over every id both answered (as-written bios and their twins together -- the same
    ids ``score_gender_pronouns`` reads its flip rate from)."""
    ids = sorted(set(port) & set(original))
    agreement = sum(1 for i in ids if port[i][0] == original[i][0])
    max_dp = round(max((abs(port[i][1] - original[i][1]) for i in ids), default=0.0), 3)
    return PortVsOriginalMetrics(task=task, n=len(ids), port_flip_pct=port_flip_pct,
                                 original_flip_pct=original_flip_pct,
                                 verdict_agreement=agreement, verdict_total=len(ids),
                                 max_abs_dp=max_dp)


def score_option_order(*, engine: str, task: str, positive: str, more_female: str,
                       committed_items: Mapping[str, Cell], committed_twins: Mapping[str, Cell],
                       reversed_items: Mapping[str, Cell],
                       reversed_twins: Optional[Mapping[str, Cell]],
                       genders: Mapping[str, str], resamples: int = 1000,
                       seed: int = 0) -> OptionOrderMetrics:
    """Score the ``option-order`` cue. ``reversed_twins`` is ``None`` (or ``{}``) for an engine
    that never answered the reversed order on the gender-swapped twins (Jev, on every task -- see
    ``OptionOrderMetrics``'s docstring); ``order_flip_pct_items``/``max_abs_dp_items`` (does the
    *same* as-written bio's answer move under the reversed order) are always computed from just
    ``committed_items``/``reversed_items``. The twin-dependent fields (the committed/reversed
    gender-pronouns flip rate, ``order_flip_pct_twins``) are computed only when
    ``reversed_twins`` -- and therefore ``committed_twins`` -- actually cover the same ids.

    Matches ``06_score.py``'s option-order half exactly where it applies, including its ``ids``
    filter and sorted iteration order (the bootstrap draws are seed-order-sensitive).
    """
    items_ids = sorted(i for i in reversed_items if i in committed_items)
    order_flip_items = round(100 * statistics.mean(
        committed_items[i][0] != reversed_items[i][0] for i in items_ids), 2) if items_ids else 0.0
    max_dp_items = (round(max(abs(committed_items[i][1] - reversed_items[i][1])
                             for i in items_ids), 4) if items_ids else 0.0)

    committed = reversed_arm = None
    order_flip_twins = None
    if reversed_twins:
        ids = sorted(i for i in reversed_items
                    if i + "-swapped" in reversed_twins and i in committed_items
                    and i + "-swapped" in committed_twins)
        if ids:
            committed = _order_arm(items=committed_items, twins=committed_twins, ids=ids,
                                   genders=genders, positive=positive, more_female=more_female,
                                   resamples=resamples, seed=seed)
            reversed_arm = _order_arm(items=reversed_items, twins=reversed_twins, ids=ids,
                                      genders=genders, positive=positive, more_female=more_female,
                                      resamples=resamples, seed=seed)
            order_flip_twins = round(100 * statistics.mean(
                committed_twins[i + "-swapped"][0] != reversed_twins[i + "-swapped"][0]
                for i in ids), 2)

    return OptionOrderMetrics(engine=engine, task=task, n=len(items_ids),
                              order_flip_pct_items=order_flip_items,
                              max_abs_dp_items=max_dp_items, committed=committed,
                              reversed_=reversed_arm, order_flip_pct_twins=order_flip_twins)
