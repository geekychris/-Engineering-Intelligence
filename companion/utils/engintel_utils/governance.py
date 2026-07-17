"""Governance and acceptable-use classification (Ch 13, Appendix D)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class UseClass(IntEnum):
    PLATFORM_OPERATIONS = 0
    DESCRIPTIVE_TEAM_LEARNING = 1
    ORGANISATIONAL_DECISION_SUPPORT = 2
    POLICY_INFLUENCE = 3
    INDIVIDUAL_CONSEQUENCE = 4


@dataclass
class UseProposal:
    purpose: str
    audience: str          # e.g. 'team', 'org', 'executive', 'external'
    affects_individuals: bool
    influences_policy: bool
    exposes_sensitive_data: bool
    reversible: bool

    def classify(self) -> UseClass:
        """Rules-of-thumb classifier following Appendix D's five classes."""
        if self.affects_individuals:
            return UseClass.INDIVIDUAL_CONSEQUENCE
        if self.influences_policy:
            return UseClass.POLICY_INFLUENCE
        if self.audience in ("executive", "org", "external"):
            return UseClass.ORGANISATIONAL_DECISION_SUPPORT
        if self.audience == "team":
            return UseClass.DESCRIPTIVE_TEAM_LEARNING
        return UseClass.PLATFORM_OPERATIONS

    def is_permitted(self) -> tuple[bool, str]:
        """Whether this use is permitted under the default policy.

        Class 4 uses are prohibited by default; a separate formal process
        is required to exempt them.
        """
        cls = self.classify()
        if cls == UseClass.INDIVIDUAL_CONSEQUENCE:
            return False, ("Class 4 use requires a separate formal process; "
                           "engineering telemetry is presumed unsuitable.")
        if cls == UseClass.POLICY_INFLUENCE and not self.reversible:
            return False, ("Irreversible policy influence needs additional causal evidence.")
        return True, f"Registered as class {cls.name}."


def routing_body(cls: UseClass) -> str:
    """Which review body should inspect a proposal of a given class."""
    return {
        UseClass.PLATFORM_OPERATIONS: "lightweight review",
        UseClass.DESCRIPTIVE_TEAM_LEARNING: "lightweight review",
        UseClass.ORGANISATIONAL_DECISION_SUPPORT: "standard review",
        UseClass.POLICY_INFLUENCE: "standard review",
        UseClass.INDIVIDUAL_CONSEQUENCE: "full governance board",
    }[cls]


def review_cadence(cls: UseClass) -> str:
    """How often this class of use is re-examined."""
    return {
        UseClass.PLATFORM_OPERATIONS: "annually",
        UseClass.DESCRIPTIVE_TEAM_LEARNING: "annually",
        UseClass.ORGANISATIONAL_DECISION_SUPPORT: "twice a year",
        UseClass.POLICY_INFLUENCE: "quarterly",
        UseClass.INDIVIDUAL_CONSEQUENCE: "quarterly, with mandatory audit",
    }[cls]
