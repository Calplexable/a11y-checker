#!/usr/bin/env python3
"""
cli.py

Command-line interface for the accessibility checker.

Usage:
    python cli.py --url https://example.com
    python cli.py --file path/to/page.html
    python cli.py --url https://example.com --format json
    python cli.py --url https://example.com --output report.json --format json
"""

import argparse
import json
import sys

from checker import check_html, check_url
from checker.models import Severity

SEVERITY_LABELS = {
    Severity.ERROR: "ERROR",
    Severity.WARNING: "WARN ",
    Severity.INFO: "INFO ",
}


def print_text_report(report) -> None:
    print(f"\nAccessibility report for: {report.source}")
    print(f"Score: {report.score}/100")
    print(
        f"Errors: {report.error_count}  Warnings: {report.warning_count}  Info: {report.info_count}"
    )
    print("-" * 70)

    if not report.issues:
        print("No issues found by the automated checks. 🎉")
        print(
            "Note: automated checks only catch a subset of accessibility "
            "issues. Manual review is still recommended."
        )
        return

    for issue in report.issues:
        label = SEVERITY_LABELS[issue.severity]
        print(f"[{label}] {issue.rule_id} — {issue.message}")
        print(f"        {issue.wcag_ref}")
        if issue.element:
            print(f"        Element: {issue.element}")
        if issue.suggestion:
            print(f"        Fix: {issue.suggestion}")
        print()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Check an HTML page for common accessibility issues."
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--url", help="URL of the page to check")
    source_group.add_argument("--file", help="Path to a local HTML file to check")

    parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format (default: text)"
    )
    parser.add_argument(
        "--output", help="Write the report to this file instead of stdout"
    )

    args = parser.parse_args(argv)

    try:
        if args.url:
            report = check_url(args.url)
        else:
            with open(args.file, "r", encoding="utf-8") as f:
                html = f.read()
            report = check_html(html, source=args.file)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1
    except Exception as exc:  # network errors, parse errors, etc.
        print(f"Error checking {'URL' if args.url else 'file'}: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        output = json.dumps(report.to_dict(), indent=2)
    else:
        # Capture text output to a string so --output works for both formats
        import io
        import contextlib

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            print_text_report(report)
        output = buf.getvalue()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Report written to {args.output}")
    else:
        print(output)

    # Non-zero exit code if there are errors, useful for CI pipelines
    return 1 if report.error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
