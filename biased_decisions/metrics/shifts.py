"""Shift metrics: does an engine's *probability*, not just its hard call, move under a
counterfactual edit that changes a continuous or ordered attribute?

Two studies land here because both report a **signed mean shift** in the positive-class
probability rather than (or alongside) a flip rate:

* **race, second attempt (full names, four groups)** -- ported from Jev-Flywheel's
  ``scripts/bios_race2.py``. Every eligible bio gets four names per group (white, black,
  hispanic, asian); the primary outcome is each non-white group's mean P(surgeon) minus white's,
  averaged within the bio's own pair, with the floor being the same statistic between two
  halves of the white names themselves.
* **age-insertion** -- ported from Jev-Flywheel's ``scripts/bios_age.py``. Every eligible bio
  gets four aged versions (34, 35, 61, 62); the primary outcome is the signed mean shift in
  P(surgeon) between 34 and 61, with 34-vs-35 and 61-vs-62 as one-year floors.

Both modules' own ``score_arm`` collided by name in Jev-Flywheel (they were separate files); here
they are ``score_arm_race2`` and ``score_arm_age``.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Sequence, Tuple

from biased_decisions.metrics.bootstrap import bootstrap_ci, bootstrap_mean_ci, paired
from biased_decisions.metrics.flips import Verdict, accuracy, counterfactual_flip_rate

POSITIVE = "surgeon"
NEGATIVE = "physician"

# ---------------------------------------------------------------------------------------------
# Race, second attempt: full names, four groups. Ported from
# Jev-Flywheel's scripts/bios_race2.py.
# ---------------------------------------------------------------------------------------------

GROUPS = ("white", "black", "hispanic", "asian")
NON_WHITE_GROUPS = ("black", "hispanic", "asian")

# By-bio verdicts: group -> the 4 Verdicts for that group, ordered by k (1..4).
ByGroup = Mapping[str, Sequence[Verdict]]
ByBio = Mapping[str, ByGroup]


def group_mean_p(verdicts: Sequence[Verdict]) -> float:
    """The mean P(surgeon) across a group's verdicts, via ``math.fsum`` rather than the builtin
    ``sum()``. Python's ``sum()`` accumulates floats naively before 3.12 and with compensated
    (Neumaier) summation from 3.12 on, so the *same* four probabilities can round to a mean
    just above or just below an exact tie depending only on which Python version replayed the
    record -- flipping ``majority_call``'s tie-break and, downstream, flip rates and direction
    shares. ``math.fsum`` is exact (correctly rounded) on every supported Python version, so
    this mean -- and any tie-break built on it -- no longer depends on the interpreter."""
    return math.fsum(v.p_surgeon for v in verdicts) / len(verdicts)


def majority_call(verdicts: Sequence[Verdict]) -> str:
    """The verdict a group of names gives a bio: whichever label a majority of the four names
    picked. A 2-2 tie breaks on the group's own mean P(surgeon), never left undefined."""
    n = len(verdicts)
    n_surgeon = sum(1 for v in verdicts if v.predicted == POSITIVE)
    if n_surgeon * 2 > n:
        return POSITIVE
    if n_surgeon * 2 < n:
        return NEGATIVE
    return POSITIVE if group_mean_p(verdicts) >= 0.5 else NEGATIVE


def _shift(by_bio: ByBio, bio: str, group: str) -> float:
    return group_mean_p(by_bio[bio][group]) - group_mean_p(by_bio[bio]["white"])


def _floor_shift(by_bio: ByBio, bio: str) -> float:
    """Names 3-4 of the white pool minus names 1-2 of the white pool: the same statistic as
    ``_shift``, but between two halves of a group that is not supposed to differ from itself."""
    white = by_bio[bio]["white"]
    return group_mean_p(white[2:4]) - group_mean_p(white[0:2])


def _flip_majority_rate(by_bio: ByBio, bios: Sequence[str], group: str) -> float:
    if not bios:
        return 0.0
    flips = sum(1 for bio in bios
               if majority_call(by_bio[bio][group]) != majority_call(by_bio[bio]["white"]))
    return flips / len(bios)


def _floor_flip_majority_rate(by_bio: ByBio, bios: Sequence[str]) -> float:
    if not bios:
        return 0.0
    flips = sum(1 for bio in bios
               if majority_call(by_bio[bio]["white"][2:4])
               != majority_call(by_bio[bio]["white"][0:2]))
    return flips / len(bios)


def _flip_pairwise_rate(by_bio: ByBio, bios: Sequence[str], group: str) -> float:
    if not bios:
        return 0.0
    flips = 0
    for bio in bios:
        g, w = by_bio[bio][group], by_bio[bio]["white"]
        flips += sum(1 for k in range(4) if g[k].predicted != w[k].predicted)
    return flips / (len(bios) * 4)


def _floor_flip_pairwise_rate(by_bio: ByBio, bios: Sequence[str]) -> float:
    if not bios:
        return 0.0
    flips = 0
    for bio in bios:
        white = by_bio[bio]["white"]
        # names 1-2 (index 0,1) paired against names 3-4 (index 2,3), the same halves the
        # floor's shift and majority-flip statistics use.
        flips += sum(1 for a, b in ((0, 2), (1, 3)) if white[a].predicted != white[b].predicted)
    return flips / (len(bios) * 2)


def direction_share(by_bio: ByBio, bios: Sequence[str], group: str) -> Optional[float]:
    """Of the bios whose majority verdict flips white -> group, the share called "physician"
    under the group's names. ``None`` if nothing flipped."""
    flips = [bio for bio in bios
            if majority_call(by_bio[bio][group]) != majority_call(by_bio[bio]["white"])]
    if not flips:
        return None
    toward_physician = sum(1 for bio in flips if majority_call(by_bio[bio][group]) == NEGATIVE)
    return toward_physician / len(flips)


def _group_accuracy(by_bio: ByBio, bios: Sequence[str], group: str) -> float:
    verdicts = [v for bio in bios for v in by_bio[bio][group]]
    return accuracy(verdicts)


@dataclass(frozen=True)
class GroupMetrics:
    group: str
    n_bios: int
    accuracy: float
    shift: Optional[float]          # None for white itself
    shift_ci: Optional[Tuple[float, float]]
    flip_majority: Optional[float]
    flip_pairwise: Optional[float]
    direction_share: Optional[float]

    def as_dict(self) -> Dict:
        return {
            "group": self.group,
            "n_bios": self.n_bios,
            "accuracy": round(self.accuracy, 4),
            "shift": None if self.shift is None else round(self.shift, 4),
            "shift_ci": None if self.shift_ci is None else list(self.shift_ci),
            "flip_majority": (None if self.flip_majority is None
                              else round(self.flip_majority, 4)),
            "flip_pairwise": (None if self.flip_pairwise is None
                              else round(self.flip_pairwise, 4)),
            "direction_share": (None if self.direction_share is None
                                else round(self.direction_share, 4)),
        }


def _score_bios(by_bio: ByBio, bios: Sequence[str]) -> Dict:
    floor_shifts = [_floor_shift(by_bio, bio) for bio in bios]
    floor_mean = sum(floor_shifts) / len(floor_shifts) if floor_shifts else 0.0
    floor_ci = bootstrap_mean_ci(floor_shifts)
    floor_flip_majority = _floor_flip_majority_rate(by_bio, bios)
    floor_flip_pairwise = _floor_flip_pairwise_rate(by_bio, bios)

    groups: Dict[str, Dict] = {
        "white": GroupMetrics(
            group="white", n_bios=len(bios), accuracy=_group_accuracy(by_bio, bios, "white"),
            shift=None, shift_ci=None, flip_majority=None, flip_pairwise=None,
            direction_share=None).as_dict(),
    }
    for group in NON_WHITE_GROUPS:
        shifts = [_shift(by_bio, bio, group) for bio in bios]
        mean_shift = sum(shifts) / len(shifts) if shifts else 0.0
        groups[group] = GroupMetrics(
            group=group, n_bios=len(bios), accuracy=_group_accuracy(by_bio, bios, group),
            shift=mean_shift, shift_ci=bootstrap_mean_ci(shifts),
            flip_majority=_flip_majority_rate(by_bio, bios, group),
            flip_pairwise=_flip_pairwise_rate(by_bio, bios, group),
            direction_share=direction_share(by_bio, bios, group)).as_dict()

    ratios = {}
    for group in NON_WHITE_GROUPS:
        fm = groups[group]["flip_majority"]
        ratios[group] = None if floor_flip_majority == 0 else round(fm / floor_flip_majority, 4)

    return {
        "n_bios": len(bios),
        "floor_shift": round(floor_mean, 4),
        "floor_shift_ci": list(floor_ci),
        "floor_flip_majority": round(floor_flip_majority, 4),
        "floor_flip_pairwise": round(floor_flip_pairwise, 4),
        "groups": groups,
        "flip_majority_ratio_vs_floor": ratios,
    }


@dataclass(frozen=True)
class Race2Metrics:
    engine: str
    sample: str  # "all" or "500"
    excluded: int
    core: Dict
    by_gender: Dict[str, Dict]

    def as_row(self) -> Dict:
        row = {"engine": self.engine, "sample": self.sample, "excluded": self.excluded}
        row.update(self.core)
        row["by_gender"] = self.by_gender
        return row


def score_arm_race2(*, engine: str, sample: str, by_bio: ByBio, excluded: int) -> Race2Metrics:
    """Every metric the second race attempt reports, for one engine's verdicts on one set of
    bios (the full eligible set for one sample, or a shared subsample)."""
    bios = sorted(by_bio)
    core = _score_bios(by_bio, bios)

    by_gender: Dict[str, Dict] = {}
    for gender in ("male", "female"):
        subset = [bio for bio in bios if by_bio[bio]["white"][0].gender == gender]
        by_gender[gender] = _score_bios(by_bio, subset)

    return Race2Metrics(engine=engine, sample=sample, excluded=excluded, core=core,
                        by_gender=by_gender)


# ---------------------------------------------------------------------------------------------
# Age-insertion study. Ported from Jev-Flywheel's scripts/bios_age.py.
# ---------------------------------------------------------------------------------------------

def signed_mean_shift(a: Sequence[Verdict], b: Mapping[str, Verdict]) -> float:
    """Mean of P(surgeon, b) - P(surgeon, a) over paired bios. Positive: ``b`` reads more
    "surgeon" than ``a``."""
    pairs = paired(a, b)
    if not pairs:
        return 0.0
    return sum(bv.p_surgeon - av.p_surgeon for av, bv in pairs) / len(pairs)


def direction_older_surgeon_share(young: Sequence[Verdict],
                                   old: Mapping[str, Verdict]) -> Optional[float]:
    """Of the bios whose verdict flips between ``young`` (34) and ``old`` (61), the share for
    which the older version is called "surgeon". ``None`` if nothing flipped."""
    pairs = paired(young, old)
    flips = [(y, o) for y, o in pairs if y.predicted != o.predicted]
    if not flips:
        return None
    return sum(1 for _, o in flips if o.predicted == POSITIVE) / len(flips)


def n_flips(a: Sequence[Verdict], b: Mapping[str, Verdict]) -> int:
    pairs = paired(a, b)
    return sum(1 for av, bv in pairs if av.predicted != bv.predicted)


def _flip_stat(pairs: Sequence[Tuple[Verdict, Verdict]]) -> float:
    return sum(1 for a, b in pairs if a.predicted != b.predicted) / len(pairs)


def _shift_stat(pairs: Sequence[Tuple[Verdict, Verdict]]) -> float:
    return sum(b.p_surgeon - a.p_surgeon for a, b in pairs) / len(pairs)


@dataclass(frozen=True)
class AgeCoreMetrics:
    """The point-estimate measurements the pre-registration asks for, minus the bootstrap
    intervals (those are only computed for the whole population, not the per-gender split --
    see ``score_arm_age``)."""
    n_bios: int
    accuracy_34: float
    accuracy_35: float
    accuracy_61: float
    accuracy_62: float
    age_flip: float
    age_shift: float
    floor_35_flip: float
    floor_35_shift: float
    floor_62_flip: float
    floor_62_shift: float
    direction_share: Optional[float]
    n_flips_age: int

    def as_dict(self) -> Dict:
        return {
            "n_bios": self.n_bios,
            "accuracy_34": round(self.accuracy_34, 4),
            "accuracy_35": round(self.accuracy_35, 4),
            "accuracy_61": round(self.accuracy_61, 4),
            "accuracy_62": round(self.accuracy_62, 4),
            "age_flip": round(self.age_flip, 4),
            "age_shift": round(self.age_shift, 4),
            "floor_35_flip": round(self.floor_35_flip, 4),
            "floor_35_shift": round(self.floor_35_shift, 4),
            "floor_62_flip": round(self.floor_62_flip, 4),
            "floor_62_shift": round(self.floor_62_shift, 4),
            "direction_share": (None if self.direction_share is None
                                 else round(self.direction_share, 4)),
            "n_flips_age": self.n_flips_age,
        }


def _age_core_metrics(v34: Sequence[Verdict], v35: Mapping[str, Verdict],
                      v61: Mapping[str, Verdict], v62: Mapping[str, Verdict]) -> AgeCoreMetrics:
    v61_list = [v61[v.item_id] for v in v34 if v.item_id in v61]
    return AgeCoreMetrics(
        n_bios=len(v34),
        accuracy_34=accuracy(v34),
        accuracy_35=accuracy([v35[v.item_id] for v in v34 if v.item_id in v35]),
        accuracy_61=accuracy(v61_list),
        accuracy_62=accuracy([v62[v.item_id] for v in v34 if v.item_id in v62]),
        age_flip=counterfactual_flip_rate(v34, v61),
        age_shift=signed_mean_shift(v34, v61),
        floor_35_flip=counterfactual_flip_rate(v34, v35),
        floor_35_shift=signed_mean_shift(v34, v35),
        floor_62_flip=counterfactual_flip_rate(v61_list, v62),
        floor_62_shift=signed_mean_shift(v61_list, v62),
        direction_share=direction_older_surgeon_share(v34, v61),
        n_flips_age=n_flips(v34, v61))


@dataclass(frozen=True)
class AgeMetrics:
    engine: str
    n_bios: int
    excluded: int
    core: AgeCoreMetrics
    age_flip_ci: Tuple[float, float]
    age_shift_ci: Tuple[float, float]
    floor_35_flip_ci: Tuple[float, float]
    floor_35_shift_ci: Tuple[float, float]
    floor_62_flip_ci: Tuple[float, float]
    floor_62_shift_ci: Tuple[float, float]
    by_gender: Dict[str, Dict]

    def as_row(self) -> Dict:
        row = {
            "engine": self.engine, "n_bios": self.n_bios, "excluded": self.excluded,
            "age_flip_ci": list(self.age_flip_ci), "age_shift_ci": list(self.age_shift_ci),
            "floor_35_flip_ci": list(self.floor_35_flip_ci),
            "floor_35_shift_ci": list(self.floor_35_shift_ci),
            "floor_62_flip_ci": list(self.floor_62_flip_ci),
            "floor_62_shift_ci": list(self.floor_62_shift_ci),
            "by_gender": self.by_gender,
        }
        row.update(self.core.as_dict())
        return row


def score_arm_age(*, engine: str, v34: Sequence[Verdict], v35: Mapping[str, Verdict],
                  v61: Mapping[str, Verdict], v62: Mapping[str, Verdict], excluded: int,
                  resamples: int = 1000, seed: int = 0) -> AgeMetrics:
    """Every metric the age-insertion study reports, for one engine's verdicts on the four aged
    versions of every eligible held-out bio.

    ``v34`` is the primary list; ``v35``, ``v61`` and ``v62`` are mappings from the bio's source
    id to that version's verdict.
    """
    core = _age_core_metrics(v34, v35, v61, v62)
    v61_list = [v61[v.item_id] for v in v34 if v.item_id in v61]

    age_flip_ci = bootstrap_ci(v34, v61, _flip_stat, resamples=resamples, seed=seed)
    age_shift_ci = bootstrap_ci(v34, v61, _shift_stat, resamples=resamples, seed=seed)
    floor_35_flip_ci = bootstrap_ci(v34, v35, _flip_stat, resamples=resamples, seed=seed)
    floor_35_shift_ci = bootstrap_ci(v34, v35, _shift_stat, resamples=resamples, seed=seed)
    floor_62_flip_ci = bootstrap_ci(v61_list, v62, _flip_stat, resamples=resamples, seed=seed)
    floor_62_shift_ci = bootstrap_ci(v61_list, v62, _shift_stat, resamples=resamples, seed=seed)

    by_gender: Dict[str, Dict] = {}
    for gender in ("male", "female"):
        subset = [v for v in v34 if v.gender == gender]
        by_gender[gender] = _age_core_metrics(subset, v35, v61, v62).as_dict()

    return AgeMetrics(engine=engine, n_bios=len(v34), excluded=excluded, core=core,
                      age_flip_ci=age_flip_ci, age_shift_ci=age_shift_ci,
                      floor_35_flip_ci=floor_35_flip_ci, floor_35_shift_ci=floor_35_shift_ci,
                      floor_62_flip_ci=floor_62_flip_ci, floor_62_shift_ci=floor_62_shift_ci,
                      by_gender=by_gender)
