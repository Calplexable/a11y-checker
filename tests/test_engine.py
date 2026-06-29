import unittest

from checker.models import Report, Issue, Severity
from checker.engine import check_html


class TestReportScoring(unittest.TestCase):
    def test_empty_report_scores_100(self):
        report = Report(source="test")
        self.assertEqual(report.score, 100)
        self.assertEqual(report.error_count, 0)

    def test_errors_reduce_score_more_than_warnings(self):
        report_errors = Report(source="test")
        report_errors.add(
            Issue(rule_id="x", severity=Severity.ERROR, message="m", wcag_ref="w")
        )

        report_warnings = Report(source="test")
        report_warnings.add(
            Issue(rule_id="x", severity=Severity.WARNING, message="m", wcag_ref="w")
        )

        self.assertLess(report_errors.score, report_warnings.score)

    def test_score_does_not_go_below_zero(self):
        report = Report(source="test")
        for _ in range(50):
            report.add(Issue(rule_id="x", severity=Severity.ERROR, message="m", wcag_ref="w"))
        self.assertEqual(report.score, 0)

    def test_counts_by_severity(self):
        report = Report(source="test")
        report.add(Issue(rule_id="a", severity=Severity.ERROR, message="m", wcag_ref="w"))
        report.add(Issue(rule_id="b", severity=Severity.WARNING, message="m", wcag_ref="w"))
        report.add(Issue(rule_id="c", severity=Severity.WARNING, message="m", wcag_ref="w"))
        report.add(Issue(rule_id="d", severity=Severity.INFO, message="m", wcag_ref="w"))

        self.assertEqual(report.error_count, 1)
        self.assertEqual(report.warning_count, 2)
        self.assertEqual(report.info_count, 1)

    def test_to_dict_structure(self):
        report = Report(source="https://example.com")
        report.add(Issue(rule_id="a", severity=Severity.ERROR, message="m", wcag_ref="w"))
        d = report.to_dict()
        self.assertEqual(d["source"], "https://example.com")
        self.assertIn("score", d)
        self.assertEqual(len(d["issues"]), 1)


class TestCheckHtmlIntegration(unittest.TestCase):
    def test_clean_page_has_high_score(self):
        html = """
        <html lang="en">
        <head><title>A Clean Page</title></head>
        <body>
            <h1>Welcome</h1>
            <p>Some text.</p>
            <img src="cat.jpg" alt="A tabby cat sleeping on a windowsill">
            <a href="/about">Learn about our mission</a>
        </body>
        </html>
        """
        report = check_html(html, source="test")
        self.assertEqual(report.error_count, 0)

    def test_messy_page_flags_multiple_issues(self):
        html = """
        <html>
        <body>
            <img src="cat.jpg">
            <input type="text" id="email">
            <a href="/report">click here</a>
            <h3>Skipped to h3</h3>
        </body>
        </html>
        """
        report = check_html(html, source="test")
        self.assertGreater(report.error_count, 0)
        self.assertGreater(report.warning_count, 0)
        rule_ids = {i.rule_id for i in report.issues}
        self.assertIn("img-alt-missing", rule_ids)
        self.assertIn("input-missing-label", rule_ids)
        self.assertIn("html-lang-missing", rule_ids)
        self.assertIn("title-missing", rule_ids)

    def test_source_label_preserved(self):
        report = check_html("<html></html>", source="my-source-label")
        self.assertEqual(report.source, "my-source-label")


if __name__ == "__main__":
    unittest.main()
