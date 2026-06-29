"""
rules.py

Individual accessibility checks, each operating on a BeautifulSoup-parsed
document and returning a list of Issue objects. Kept as small, focused
functions so they're easy to test individually and easy to extend.

These checks cover common, well-established WCAG 2.1 failure points.
They are NOT a substitute for a full manual or automated audit (e.g.
axe-core, WAVE) — this is a portfolio-scale tool that catches the most
frequent, highest-impact issues.
"""

import re
from bs4 import BeautifulSoup

from .models import Issue, Severity

# Generic ALT text that signals the author didn't actually describe the image
PLACEHOLDER_ALT_PATTERNS = [
    r"^image$", r"^img$", r"^photo$", r"^picture$", r"^graphic$",
    r"^untitled$", r"^dsc\d*$", r"^img_?\d*$", r"^icon$",
]

# Vague link text that gives screen reader users no context out of context
VAGUE_LINK_TEXT = {
    "click here", "here", "read more", "more", "link", "this link",
    "learn more", "more info", "details",
}


def _snippet(tag) -> str:
    """Return a short, readable snippet of a tag for issue context."""
    s = str(tag)
    return s if len(s) <= 120 else s[:117] + "..."


def check_images_missing_alt(soup: BeautifulSoup) -> list:
    """WCAG 1.1.1 - all <img> need an alt attribute (can be alt="" if decorative)."""
    issues = []
    for img in soup.find_all("img"):
        if img.get("alt") is None:
            issues.append(
                Issue(
                    rule_id="img-alt-missing",
                    severity=Severity.ERROR,
                    message="Image has no alt attribute at all.",
                    wcag_ref="WCAG 1.1.1 (Non-text Content)",
                    element=_snippet(img),
                    suggestion=(
                        'Add alt="description of the image", or alt="" if the '
                        "image is purely decorative."
                    ),
                )
            )
    return issues


def check_images_placeholder_alt(soup: BeautifulSoup) -> list:
    """Flags alt text that's present but unhelpful (e.g. alt="image")."""
    issues = []
    for img in soup.find_all("img"):
        alt = img.get("alt")
        if alt and alt.strip():
            normalized = alt.strip().lower()
            if any(re.match(pattern, normalized) for pattern in PLACEHOLDER_ALT_PATTERNS):
                issues.append(
                    Issue(
                        rule_id="img-alt-placeholder",
                        severity=Severity.WARNING,
                        message=f'Image alt text ("{alt}") is generic and not descriptive.',
                        wcag_ref="WCAG 1.1.1 (Non-text Content)",
                        element=_snippet(img),
                        suggestion="Describe what the image actually shows or conveys.",
                    )
                )
    return issues


def check_form_inputs_missing_labels(soup: BeautifulSoup) -> list:
    """WCAG 1.3.1 / 4.1.2 - inputs need an associated <label>, aria-label, or aria-labelledby."""
    issues = []
    labelled_ids = {
        label.get("for") for label in soup.find_all("label") if label.get("for")
    }

    for input_tag in soup.find_all(["input", "textarea", "select"]):
        input_type = (input_tag.get("type") or "").lower()
        if input_type in ("hidden", "submit", "button", "reset"):
            continue

        has_id_label = input_tag.get("id") in labelled_ids
        has_aria_label = bool(input_tag.get("aria-label"))
        has_aria_labelledby = bool(input_tag.get("aria-labelledby"))
        wrapped_in_label = input_tag.find_parent("label") is not None

        if not (has_id_label or has_aria_label or has_aria_labelledby or wrapped_in_label):
            issues.append(
                Issue(
                    rule_id="input-missing-label",
                    severity=Severity.ERROR,
                    message=f"<{input_tag.name}> has no associated label.",
                    wcag_ref="WCAG 1.3.1 (Info and Relationships) / 4.1.2 (Name, Role, Value)",
                    element=_snippet(input_tag),
                    suggestion=(
                        "Add a <label for=\"id\"> pointing at this field's id, or "
                        "an aria-label attribute."
                    ),
                )
            )
    return issues


def check_heading_hierarchy(soup: BeautifulSoup) -> list:
    """WCAG 1.3.1 - heading levels shouldn't skip (e.g. h1 -> h3 with no h2)."""
    issues = []
    headings = soup.find_all(re.compile(r"^h[1-6]$"))
    if not headings:
        return issues

    levels = [int(h.name[1]) for h in headings]

    if levels[0] != 1:
        issues.append(
            Issue(
                rule_id="heading-no-h1",
                severity=Severity.WARNING,
                message=f"Page's first heading is <h{levels[0]}>, not <h1>.",
                wcag_ref="WCAG 1.3.1 (Info and Relationships)",
                element=_snippet(headings[0]),
                suggestion="Start the page's heading structure with a single <h1>.",
            )
        )

    for i in range(1, len(levels)):
        if levels[i] - levels[i - 1] > 1:
            issues.append(
                Issue(
                    rule_id="heading-skipped-level",
                    severity=Severity.WARNING,
                    message=(
                        f"Heading level jumps from h{levels[i - 1]} to h{levels[i]} "
                        "without an intermediate level."
                    ),
                    wcag_ref="WCAG 1.3.1 (Info and Relationships)",
                    element=_snippet(headings[i]),
                    suggestion="Don't skip heading levels; nest them sequentially.",
                )
            )
    return issues


def check_vague_link_text(soup: BeautifulSoup) -> list:
    """WCAG 2.4.4 - link text should make sense out of context (screen reader users often tab through links alone)."""
    issues = []
    for link in soup.find_all("a"):
        text = link.get_text(strip=True).lower()
        if text in VAGUE_LINK_TEXT:
            issues.append(
                Issue(
                    rule_id="link-vague-text",
                    severity=Severity.WARNING,
                    message=f'Link text "{link.get_text(strip=True)}" is not descriptive out of context.',
                    wcag_ref="WCAG 2.4.4 (Link Purpose in Context)",
                    element=_snippet(link),
                    suggestion=(
                        'Use descriptive link text (e.g. "Download the 2025 annual report" '
                        'instead of "click here"), or add an aria-label.'
                    ),
                )
            )
    return issues


def check_empty_links(soup: BeautifulSoup) -> list:
    """A link with no text and no accessible name is invisible to screen reader users."""
    issues = []
    for link in soup.find_all("a", href=True):
        text = link.get_text(strip=True)
        has_aria_label = bool(link.get("aria-label"))
        has_img_alt = any(img.get("alt") for img in link.find_all("img"))
        if not text and not has_aria_label and not has_img_alt:
            issues.append(
                Issue(
                    rule_id="link-empty",
                    severity=Severity.ERROR,
                    message="Link has no text content and no accessible name.",
                    wcag_ref="WCAG 2.4.4 (Link Purpose in Context) / 4.1.2",
                    element=_snippet(link),
                    suggestion="Add visible link text or an aria-label describing the link's purpose.",
                )
            )
    return issues


def check_missing_lang_attribute(soup: BeautifulSoup) -> list:
    """WCAG 3.1.1 - the <html> tag should declare the page's language."""
    issues = []
    html_tag = soup.find("html")
    if html_tag is not None and not html_tag.get("lang"):
        issues.append(
            Issue(
                rule_id="html-lang-missing",
                severity=Severity.ERROR,
                message="<html> tag is missing a lang attribute.",
                wcag_ref="WCAG 3.1.1 (Language of Page)",
                element="<html>",
                suggestion='Add a lang attribute, e.g. <html lang="en">.',
            )
        )
    return issues


def check_missing_page_title(soup: BeautifulSoup) -> list:
    """WCAG 2.4.2 - every page needs a descriptive <title>."""
    issues = []
    title_tag = soup.find("title")
    if title_tag is None or not title_tag.get_text(strip=True):
        issues.append(
            Issue(
                rule_id="title-missing",
                severity=Severity.ERROR,
                message="Page has no <title> element, or it's empty.",
                wcag_ref="WCAG 2.4.2 (Page Titled)",
                element="<title>" if title_tag is None else _snippet(title_tag),
                suggestion="Add a descriptive <title> summarizing the page's content/purpose.",
            )
        )
    return issues


def check_tables_missing_headers(soup: BeautifulSoup) -> list:
    """WCAG 1.3.1 - data tables should use <th> so screen readers can announce column/row context."""
    issues = []
    for table in soup.find_all("table"):
        if not table.find("th"):
            issues.append(
                Issue(
                    rule_id="table-missing-headers",
                    severity=Severity.WARNING,
                    message="Table has no <th> header cells.",
                    wcag_ref="WCAG 1.3.1 (Info and Relationships)",
                    element=_snippet(table)[:120],
                    suggestion="Use <th> for header cells, with scope=\"col\" or scope=\"row\" as appropriate.",
                )
            )
    return issues


def check_positive_tabindex(soup: BeautifulSoup) -> list:
    """A positive tabindex disrupts the natural tab order and is widely considered bad practice."""
    issues = []
    for tag in soup.find_all(attrs={"tabindex": True}):
        try:
            value = int(tag.get("tabindex"))
        except (TypeError, ValueError):
            continue
        if value > 0:
            issues.append(
                Issue(
                    rule_id="positive-tabindex",
                    severity=Severity.WARNING,
                    message=f'tabindex="{value}" overrides natural tab order.',
                    wcag_ref="WCAG 2.4.3 (Focus Order)",
                    element=_snippet(tag),
                    suggestion='Use tabindex="0" or rely on natural DOM order instead of positive values.',
                )
            )
    return issues


# Every check function above, run in order against a parsed document.
ALL_CHECKS = [
    check_images_missing_alt,
    check_images_placeholder_alt,
    check_form_inputs_missing_labels,
    check_heading_hierarchy,
    check_vague_link_text,
    check_empty_links,
    check_missing_lang_attribute,
    check_missing_page_title,
    check_tables_missing_headers,
    check_positive_tabindex,
]
