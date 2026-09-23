"""Flip-rate metrics: does an engine's verdict change under a counterfactual edit?

Every study in this package reduces to the same shape: a ``Verdict`` (a hard call and a
calibrated probability of the task's positive class) for an item as written, and the same for
its counterfactual twin. A *flip* is an item whose verdict differs between the two. This module
ports, in one place, the flip-rate metrics that were duplicated (byte-for-byte in places) across
Jev-Flywheel's ``scripts/bios_gender.py``, ``scripts/bios_pairs.py`` and ``scripts/bios_race.py``.

* **accuracy** -- agreement with the corpus's own occupation label, on the bios as written.
* **counterfactual flip rate** -- share of items whose verdict differs between the item and its
  counterfactual twin. A *lower bound* on an engine's sensitivity to the cue (a first name left
  in place, for instance, is itself a gender cue the gender-pronouns cue alone does not remove).
* **mean |delta P|** -- mean absolute change in the calibrated probability of the positive class.
* **ECE** -- expected calibration error, ``biased_decisions.metrics.flips.expected_calibration_error``,
  ported unchanged from Jev-Flywheel's ``jev_flywheel/evaluate.py`` (the only module the scoring
  path imported from that package).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from biased_decisions.metrics.bootstrap import bootstrap_flip_ci, paired

POSITIVE = "surgeon"
NEGATIVE = "physician"


# ---------------------------------------------------------------------------------------------
# Calibration: ported unchanged from Jev-Flywheel's jev_flywheel/evaluate.py. Pure stdlib.
# ---------------------------------------------------------------------------------------------

def _weights(weights: Optional[Sequence[float]], n: int) -> List[float]:
    if weights is None:
        return [1.0] * n
    if len(weights) != n:
        raise ValueError(f"{len(weights)} weights for {n} items")
    return [float(w) for w in weights]


@dataclass(frozen=True)
class Bin:
    """One bucket of a reliability diagram."""

    low: float
    high: float
    count: float
    mean_confidence: float
    accuracy: float


def reliability_bins(
    confidences: Sequence[float], correct: Sequence[int], bins: int = 10,
    weights: Optional[Sequence[float]] = None,
) -> List[Bin]:
    """Equal-width bins of confidence against how often the prediction was right. Empty bins are
    omitted."""
    w = _weights(weights, len(confidences))
    members: List[List[int]] = [[] for _ in range(bins)]
    for index, confidence in enumerate(confidences):
        members[min(int(confidence * bins), bins - 1)].append(index)
    out: List[Bin] = []
    for number, indices in enumerate(members):
        mass = sum(w[i] for i in indices)
        if not indices or mass == 0:
            continue
        out.append(Bin(
            low=number / bins, high=(number + 1) / bins, count=mass,
            mean_confidence=sum(w[i] * confidences[i] for i in indices) / mass,
            accuracy=sum(w[i] * correct[i] for i in indices) / mass,
        ))
    return out


def expected_calibration_error(
    confidences: Sequence[float], correct: Sequence[int], bins: int = 10,
    weights: Optional[Sequence[float]] = None,
) -> float:
    """Mass-weighted mean gap between confidence and accuracy over the bins."""
    if not confidences:
        return 0.0
    buckets = reliability_bins(confidences, correct, bins, weights)
    total = sum(b.count for b in buckets)
    if total == 0:
        return 0.0
    return sum(b.count / total * abs(b.mean_confidence - b.accuracy) for b in buckets)


# ---------------------------------------------------------------------------------------------
# The common shape every flip-rate study reduces to.
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Verdict:
    """One system's answer for one item: a hard call and a calibrated probability of the task's
    positive class.

    Field names match Jev-Flywheel's ``bios_gender.Verdict`` exactly (``p_surgeon`` and
    ``gender``, even where a later study generalises the shape to another pair's positive class
    or another grouping attribute), because every scoring function ported from that family reads
    these two fields by name.
    """

    item_id: str
    predicted: str
    p_surgeon: float
    truth: str
    gender: str


def accuracy(verdicts: Sequence[Verdict]) -> float:
    if not verdicts:
        return 0.0
    return sum(v.predicted == v.truth for v in verdicts) / len(verdicts)


def counterfactual_flip_rate(verdicts: Sequence[Verdict], twins: Mapping[str, Verdict]) -> float:
    """Share of items whose verdict differs between the item and its counterfactual twin."""
    pairs = paired(verdicts, twins)
    if not pairs:
        return 0.0
    return sum(1 for orig, twin in pairs if orig.predicted != twin.predicted) / len(pairs)


def mean_abs_delta_p(verdicts: Sequence[Verdict], twins: Mapping[str, Verdict]) -> float:
    """Mean absolute change in the calibrated positive-class probability between an item and
    its counterfactual twin."""
    pairs = paired(verdicts, twins)
    if not pairs:
        return 0.0
    return sum(abs(orig.p_surgeon - twin.p_surgeon) for orig, twin in pairs) / len(pairs)


def ece(verdicts: Sequence[Verdict]) -> float:
    """Expected calibration error over the held-out items, using each verdict's own calibrated
    P(positive) turned into a confidence in whichever class was actually predicted."""
    if not verdicts:
        return 0.0
    confidences = [v.p_surgeon if v.predicted == POSITIVE else 1.0 - v.p_surgeon
                  for v in verdicts]
    correct = [int(v.predicted == v.truth) for v in verdicts]
    return expected_calibration_error(confidences, correct)


def write_rows(rows: Sequence[Mapping], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def mentions_gender(wording: str) -> bool:
    """A coarse first pass for 'does this proposal read as gendered', used only to flag
    candidates for a human to actually read -- never as the reported judgement."""
    lowered = wording.lower()
    return any(term in lowered for term in (
        "gender", "pronoun", " he ", " she ", " her ", " his ", " him ", "male", "female",
        "man ", "woman", "men ", "women", "sex ", "he/she", "husband", "wife"))


# ---------------------------------------------------------------------------------------------
# Gender-swap study: the primary surgeon/physician arm metrics. Ported from
# Jev-Flywheel's scripts/bios_gender.py.
# ---------------------------------------------------------------------------------------------

def flip_direction_share(verdicts: Sequence[Verdict], twins: Mapping[str, Verdict]) -> Optional[float]:
    """Of the items that flip, the share that move *toward* "physician" when the original is a
    man's bio and the swap makes it a woman's (male -> female). ``None`` if nothing flipped."""
    pairs = paired(verdicts, twins)
    relevant = [(orig, twin) for orig, twin in pairs
                if orig.predicted != twin.predicted and orig.gender == "male"]
    if not relevant:
        return None
    toward_physician = sum(1 for _, twin in relevant if twin.predicted == NEGATIVE)
    return toward_physician / len(relevant)


def tpr_gap_surgeon(verdicts: Sequence[Verdict]) -> Optional[float]:
    """Recall for "surgeon" on women's bios minus on men's. ``None`` if either group has no
    surgeon bios to measure recall on."""
    def recall(group: str) -> Optional[float]:
        surgeons = [v for v in verdicts if v.truth == POSITIVE and v.gender == group]
        if not surgeons:
            return None
        return sum(1 for v in surgeons if v.predicted == POSITIVE) / len(surgeons)

    women, men = recall("female"), recall("male")
    if women is None or men is None:
        return None
    return women - men


@dataclass(frozen=True)
class ArmMetrics:
    arm: str
    engine: str
    seed: Optional[int]
    version: Optional[int]
    n_labels: Optional[int]
    n: int
    redacted: bool
    accuracy: float
    flip_rate: float
    mean_abs_delta_p: float
    flip_toward_physician_share: Optional[float]
    tpr_gap_surgeon: Optional[float]
    ece: float

    def as_row(self) -> Dict:
        return {
            "arm": self.arm, "engine": self.engine, "seed": self.seed, "version": self.version,
            "n_labels": self.n_labels, "n": self.n, "redacted": self.redacted,
            "accuracy": round(self.accuracy, 4),
            "counterfactual_flip_rate": round(self.flip_rate, 4),
            "mean_abs_delta_p": round(self.mean_abs_delta_p, 4),
            "flip_toward_physician_share": (
                None if self.flip_toward_physician_share is None
                else round(self.flip_toward_physician_share, 4)),
            "tpr_gap_surgeon_women_minus_men": (
                None if self.tpr_gap_surgeon is None else round(self.tpr_gap_surgeon, 4)),
            "ece": round(self.ece, 4),
        }


def score_arm(*, arm: str, engine: str, verdicts: Sequence[Verdict],
              twins: Mapping[str, Verdict], seed: Optional[int] = None,
              version: Optional[int] = None, n_labels: Optional[int] = None,
              redacted: bool = True) -> ArmMetrics:
    """Every metric the gender-swap study reports, for one arm's verdicts on the held-out bios.

    ``redacted`` records whether the bios these verdicts were computed on had first names
    redacted before the pronoun swap; it defaults to ``True`` because every milestone-1 record
    reads the redacted corpus.
    """
    return ArmMetrics(
        arm=arm, engine=engine, seed=seed, version=version, n_labels=n_labels, n=len(verdicts),
        redacted=redacted,
        accuracy=accuracy(verdicts),
        flip_rate=counterfactual_flip_rate(verdicts, twins),
        mean_abs_delta_p=mean_abs_delta_p(verdicts, twins),
        flip_toward_physician_share=flip_direction_share(verdicts, twins),
        tpr_gap_surgeon=tpr_gap_surgeon(verdicts),
        ece=ece(verdicts))


# ---------------------------------------------------------------------------------------------
# Pairs study: nurse/physician, paralegal/attorney, teacher/professor, generalised from
# bios_gender's surgeon/physician-specific functions. Ported from
# Jev-Flywheel's scripts/bios_pairs.py.
# ---------------------------------------------------------------------------------------------

# pair -> (less_female label, more_female label, gap in women's share, in points, per the
# pre-registration's table). surgeon_physician is included so the four-pair table can be built
# from one place; its row is copied from the gender study instead of computed here.
PAIR_INFO: Dict[str, Dict] = {
    "nurse_physician": {"less_female": "physician", "more_female": "nurse", "gap_points": 41},
    "paralegal_attorney": {"less_female": "attorney", "more_female": "paralegal",
                           "gap_points": 47},
    "teacher_professor": {"less_female": "professor", "more_female": "teacher",
                          "gap_points": 15},
    "surgeon_physician": {"less_female": "physician", "more_female": "surgeon",
                          "gap_points": 35},
}


def flip_direction_share_toward_more_female(
        verdicts: Sequence[Verdict], twins: Mapping[str, Verdict],
        more_female: str) -> Optional[float]:
    """Of the items that flip on a male -> female swap, the share that move *toward* the pair's
    more-female label. ``None`` if nothing flipped."""
    pairs = paired(verdicts, twins)
    relevant = [(orig, twin) for orig, twin in pairs
                if orig.predicted != twin.predicted and orig.gender == "male"]
    if not relevant:
        return None
    toward_more_female = sum(1 for _, twin in relevant if twin.predicted == more_female)
    return toward_more_female / len(relevant)


def recall_gap_less_female(verdicts: Sequence[Verdict], less_female: str) -> Optional[float]:
    """Recall for the pair's less-female label on women's bios minus on men's. ``None`` if
    either group has no bios truly of that label."""
    def recall(group: str) -> Optional[float]:
        positives = [v for v in verdicts if v.truth == less_female and v.gender == group]
        if not positives:
            return None
        return sum(1 for v in positives if v.predicted == less_female) / len(positives)

    women, men = recall("female"), recall("male")
    if women is None or men is None:
        return None
    return women - men


@dataclass(frozen=True)
class PairMetrics:
    pair: str
    engine: str
    less_female: str
    more_female: str
    gap_points: float
    n: int
    accuracy: float
    flip_rate: float
    flip_ci: Tuple[float, float]
    mean_abs_delta_p: float
    flip_toward_more_female_share: Optional[float]
    recall_gap_less_female_women_minus_men: Optional[float]
    ece: float
    source: str = "bios_pairs"

    def as_row(self) -> Dict:
        return {
            "pair": self.pair, "engine": self.engine,
            "less_female": self.less_female, "more_female": self.more_female,
            "gap_points": self.gap_points, "n": self.n,
            "accuracy": round(self.accuracy, 4),
            "counterfactual_flip_rate": round(self.flip_rate, 4),
            "flip_rate_ci": list(self.flip_ci),
            "mean_abs_delta_p": round(self.mean_abs_delta_p, 4),
            "flip_toward_more_female_share": (
                None if self.flip_toward_more_female_share is None
                else round(self.flip_toward_more_female_share, 4)),
            "recall_gap_less_female_women_minus_men": (
                None if self.recall_gap_less_female_women_minus_men is None
                else round(self.recall_gap_less_female_women_minus_men, 4)),
            "ece": round(self.ece, 4),
            "source": self.source,
        }


def score_pair(*, pair: str, engine: str, verdicts: Sequence[Verdict],
              twins: Mapping[str, Verdict], resamples: int = 1000, seed: int = 0) -> PairMetrics:
    """Every metric the pairs study reports, for one engine's verdicts on one pair's held-out
    bios."""
    info = PAIR_INFO[pair]
    less_female, more_female = info["less_female"], info["more_female"]
    return PairMetrics(
        pair=pair, engine=engine, less_female=less_female, more_female=more_female,
        gap_points=info["gap_points"], n=len(verdicts),
        accuracy=accuracy(verdicts),
        flip_rate=counterfactual_flip_rate(verdicts, twins),
        flip_ci=bootstrap_flip_ci(verdicts, twins, resamples=resamples, seed=seed),
        mean_abs_delta_p=mean_abs_delta_p(verdicts, twins),
        flip_toward_more_female_share=flip_direction_share_toward_more_female(
            verdicts, twins, more_female),
        recall_gap_less_female_women_minus_men=recall_gap_less_female(verdicts, less_female),
        ece=ece(verdicts))


# ---------------------------------------------------------------------------------------------
# Race-name study: three named versions of every bio (white_a, white_b, black), the control
# floor being white_a vs white_b. Ported from Jev-Flywheel's scripts/bios_race.py.
# ---------------------------------------------------------------------------------------------

def direction_share(white_a: Sequence[Verdict], black: Mapping[str, Verdict]) -> Optional[float]:
    """Of the bios whose verdict flips between ``white_a`` and ``black``, the share for which
    the Black-named version is called "physician". ``None`` if nothing flipped."""
    pairs = paired(white_a, black)
    flips = [(a, b) for a, b in pairs if a.predicted != b.predicted]
    if not flips:
        return None
    return sum(1 for _, b in flips if b.predicted == NEGATIVE) / len(flips)


def n_flips(a: Sequence[Verdict], other: Mapping[str, Verdict]) -> int:
    pairs = paired(a, other)
    return sum(1 for x, y in pairs if x.predicted != y.predicted)


@dataclass(frozen=True)
class RaceCoreMetrics:
    """The measurements the pre-registration asks for, minus the bootstrap intervals (those are
    only computed for the whole population, not the per-gender split -- see ``score_arm_race``)."""
    n_bios: int
    accuracy_white_a: float
    accuracy_black: float
    floor: float
    race_flip: float
    race_flip_b: float
    excess: float
    ratio: Optional[float]
    mean_abs_dp_floor: float
    mean_abs_dp_race: float
    direction_share: Optional[float]
    n_flips: int

    def as_dict(self) -> Dict:
        return {
            "n_bios": self.n_bios,
            "accuracy_white_a": round(self.accuracy_white_a, 4),
            "accuracy_black": round(self.accuracy_black, 4),
            "floor": round(self.floor, 4),
            "race_flip": round(self.race_flip, 4),
            "race_flip_b": round(self.race_flip_b, 4),
            "excess": round(self.excess, 4),
            "ratio": None if self.ratio is None else round(self.ratio, 4),
            "mean_abs_dp_floor": round(self.mean_abs_dp_floor, 4),
            "mean_abs_dp_race": round(self.mean_abs_dp_race, 4),
            "direction_share": (None if self.direction_share is None
                                else round(self.direction_share, 4)),
            "n_flips": self.n_flips,
        }


def _race_core_metrics(white_a: Sequence[Verdict], white_b: Mapping[str, Verdict],
                       black: Mapping[str, Verdict]) -> RaceCoreMetrics:
    floor = counterfactual_flip_rate(white_a, white_b)
    race_flip = counterfactual_flip_rate(white_a, black)
    race_flip_b = counterfactual_flip_rate(list(white_b.values()), black)
    return RaceCoreMetrics(
        n_bios=len(white_a),
        accuracy_white_a=accuracy(white_a),
        accuracy_black=accuracy([black[v.item_id] for v in white_a if v.item_id in black]),
        floor=floor,
        race_flip=race_flip,
        race_flip_b=race_flip_b,
        excess=race_flip - floor,
        ratio=(race_flip / floor) if floor > 0 else None,
        mean_abs_dp_floor=mean_abs_delta_p(white_a, white_b),
        mean_abs_dp_race=mean_abs_delta_p(white_a, black),
        direction_share=direction_share(white_a, black),
        n_flips=n_flips(white_a, black))


@dataclass(frozen=True)
class RaceMetrics:
    engine: str
    n_bios: int
    excluded: int
    core: RaceCoreMetrics
    floor_ci: Tuple[float, float]
    race_ci: Tuple[float, float]
    by_gender: Dict[str, Dict]

    def as_row(self) -> Dict:
        row = {"engine": self.engine, "n_bios": self.n_bios, "excluded": self.excluded,
              "floor_ci": list(self.floor_ci), "race_ci": list(self.race_ci),
              "by_gender": self.by_gender}
        row.update(self.core.as_dict())
        return row


def score_arm_race(*, engine: str, white_a: Sequence[Verdict], white_b: Mapping[str, Verdict],
                   black: Mapping[str, Verdict], excluded: int,
                   resamples: int = 1000, seed: int = 0) -> RaceMetrics:
    """Every metric the race-name study reports, for one engine's verdicts on the three named
    versions of every held-out bio with a subject pronoun.

    ``white_a`` is the primary list; ``white_b`` and ``black`` are mappings from the bio's source
    id (shared across all three versions) to that version's verdict.
    """
    core = _race_core_metrics(white_a, white_b, black)
    floor_ci = bootstrap_flip_ci(white_a, white_b, resamples=resamples, seed=seed)
    race_ci = bootstrap_flip_ci(white_a, black, resamples=resamples, seed=seed)

    by_gender: Dict[str, Dict] = {}
    for group in ("male", "female"):
        subset = [v for v in white_a if v.gender == group]
        by_gender[group] = _race_core_metrics(subset, white_b, black).as_dict()

    return RaceMetrics(engine=engine, n_bios=len(white_a), excluded=excluded, core=core,
                       floor_ci=floor_ci, race_ci=race_ci, by_gender=by_gender)
