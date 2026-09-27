"""Benchmark data for laboratory work 3, variant 4."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KnapsackProblem:
    name: str
    capacity: int
    weights: tuple[int, ...]
    profits: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.weights) != len(self.profits):
            raise ValueError("weights and profits must have the same length")
        if self.capacity < 0 or any(w < 0 for w in self.weights):
            raise ValueError("capacity and weights must be non-negative")


P04 = KnapsackProblem(
    name="P04",
    capacity=50,
    weights=(31, 10, 20, 19, 4, 3, 6),
    profits=(70, 20, 39, 37, 7, 5, 10),
)


SET7 = KnapsackProblem(
    name="Набор 7",
    capacity=12828,
    weights=(
        981, 119, 419, 758, 152, 489, 40, 669, 765, 574,
        876, 314, 696, 595, 580, 457, 840, 945, 475, 665,
        61, 702, 648, 994, 822, 285, 386, 669, 23, 462,
        169, 118, 59, 769, 130, 248, 391, 872, 81, 450,
        550, 884, 820, 864, 279, 416, 359, 885, 958, 151,
    ),
    profits=(
        324, 151, 651, 73, 536, 366, 58, 508, 38, 434,
        70, 91, 425, 827, 124, 224, 628, 948, 578, 397,
        977, 47, 859, 290, 145, 118, 309, 817, 181, 582,
        639, 373, 548, 63, 60, 206, 681, 428, 315, 586,
        454, 300, 795, 699, 245, 575, 526, 876, 730, 288,
    ),
)


PROBLEMS = {P04.name: P04, SET7.name: SET7}
