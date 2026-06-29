# A11y Checker

A lightweight accessibility scanner for HTML pages. Checks for common,
high-impact WCAG 2.1 issues — missing alt text, unlabeled form fields,
broken heading hierarchy, vague link text, missing page language, and
more — and explains what's wrong and how to fix it.

Available as both a **command-line tool** and a **simple web app**.

## Why

Most accessibility tooling is either a heavyweight browser extension or
buried inside a much bigger audit platform. This is a small, focused
tool: point it at a URL or a chunk of HTML, get a plain-English report
with WCAG references and concrete fixes — no account, no setup beyond
`pip install`.

## What it checks

| Check | WCAG reference |
|---|---|
| Missing `alt` attributes on images | 1.1.1 |
| Generic/placeholder `alt` text (e.g. `alt="image"`) | 1.1.1 |
| Form fields with no associated label | 1.3.1 / 4.1.2 |
| Heading hierarchy (missing `h1`, skipped levels) | 1.3.1 |
| Vague link text (e.g. "click here") | 2.4.4 |
| Empty links with no accessible name | 2.4.4 / 4.1.2 |
| Missing `lang` attribute on `<html>` | 3.1.1 |
| Missing or empty `<title>` | 2.4.2 |
| Data tables with no `<th>` header cells | 1.3.1 |
| Positive `tabindex` values (disrupts tab order) | 2.4.3 |

Each issue includes a severity (error / warning / info), the relevant
WCAG criterion, a snippet of the offending HTML, and a suggested fix.

**This is not a replacement for a full audit.** Automated tools catch
roughly a third of real-world accessibility issues — things like color
contrast in images, logical reading order, or whether content actually
makes sense to a screen reader user still need human review and testing
with real assistive technology.

## Installation

```bash
git clone https://github.com/Calplexable/a11y-checker.git
cd a11y-checker
pip install -r requirements.txt
```

## Usage

### Command line

```bash
# Check a live URL
python cli.py --url https://example.com

# Check a local HTML file
python cli.py --file page.html

# Get JSON output instead of text
python cli.py --url https://example.com --format json

# Save the report to a file
python cli.py --url https://example.com --output report.json --format json
```

The CLI exits with status code `1` if any errors were found (handy for
CI pipelines), or `0` if the page is clean.

### Web app

```bash
cd web
python app.py
```

Then open `http://127.0.0.1:5000` and either paste a URL or paste raw
HTML directly into the form.

## Running tests

```bash
python -m unittest discover -s tests -v
```

38 tests covering every individual rule check, the scoring system, and
end-to-end integration through `check_html()`.

## Project structure

```
a11y-checker/
├── checker/
│   ├── __init__.py        # Public API: check_html(), check_url()
│   ├── engine.py          # Fetches pages and runs all checks
│   ├── rules.py           # Individual WCAG-based checks
│   └── models.py          # Issue / Report / Severity data classes
├── cli.py                 # Command-line interface
├── web/
│   ├── app.py             # Flask web wrapper
│   ├── templates/index.html
│   └── static/style.css
├── tests/
│   ├── test_rules.py
│   └── test_engine.py
└── requirements.txt
```

## Extending it

Each check in `checker/rules.py` is a small, independent function that
takes a parsed `BeautifulSoup` document and returns a list of `Issue`
objects. Adding a new check means writing one function and adding it
to the `ALL_CHECKS` list at the bottom of the file — no other code
needs to change.
