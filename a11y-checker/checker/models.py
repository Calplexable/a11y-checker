"""
models.py

Data structures shared across the accessibility checker: a single
Issue, and a Report that aggregates issues for one page/HTML document.
"""

from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    """
    Roughly maps to WCAG conformance impact:
      ERROR   - clear WCAG failure, blocks some users from using the page
      WARNING - likely problem or bad practice, not always a hard failure
      INFO    - worth reviewing, but often a judgement call (e.g. alt text quality)
    """

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Issue:
    rule_id: str          # e.g. "img-alt-missing"
    severity: Severity
    message: str           # human-readable description of the problem
    wcag_ref: str           # e.g. "WCAG 1.1.1 (Non-text Content)"
    element: str = ""       # a short snippet of the offending HTML, for context
    suggestion: str = ""    # how to fix it

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "message": self.message,
            "wcag_ref": self.wcag_ref,
            "element": self.element,
            "suggestion": self.suggestion,
        }


@dataclass
class Report:
    source: str  # URL checked, or "<pasted HTML>"
    issues: list = field(default_factory=list)

    def add(self, issue: Issue) -> None:
        self.issues.append(issue)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.INFO)

    @property
    def score(self) -> int:
        """
        A simple 0-100 score: starts at 100, errors cost more than warnings,
        floor of 0. Not a substitute for a real audit, just a quick signal.
        """
        penalty = (self.error_count * 10) + (self.warning_count * 4) + (self.info_count * 1)
        return max(0, 100 - penalty)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "score": self.score,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "issues": [i.to_dict() for i in self.issues],
        }
