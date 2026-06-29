"""
checker

A lightweight accessibility checker for HTML pages, based on common
WCAG 2.1 failure points (missing alt text, unlabeled form fields,
heading hierarchy issues, vague link text, missing page language, etc).
"""

from .engine import check_html, check_url
from .models import Report, Issue, Severity

__all__ = ["check_html", "check_url", "Report", "Issue", "Severity"]
