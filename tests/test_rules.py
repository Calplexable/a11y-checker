import unittest
from bs4 import BeautifulSoup

from checker.rules import (
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
)


def soup_of(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


class TestImageAltChecks(unittest.TestCase):
    def test_missing_alt_flagged(self):
        issues = check_images_missing_alt(soup_of('<img src="cat.jpg">'))
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "img-alt-missing")

    def test_empty_alt_is_fine(self):
        # alt="" is valid for decorative images
        issues = check_images_missing_alt(soup_of('<img src="line.png" alt="">'))
        self.assertEqual(len(issues), 0)

    def test_descriptive_alt_is_fine(self):
        issues = check_images_missing_alt(
            soup_of('<img src="cat.jpg" alt="A tabby cat sleeping on a windowsill">')
        )
        self.assertEqual(len(issues), 0)

    def test_placeholder_alt_flagged(self):
        issues = check_images_placeholder_alt(soup_of('<img src="cat.jpg" alt="image">'))
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "img-alt-placeholder")

    def test_good_alt_not_flagged_as_placeholder(self):
        issues = check_images_placeholder_alt(
            soup_of('<img src="cat.jpg" alt="A tabby cat sleeping on a windowsill">')
        )
        self.assertEqual(len(issues), 0)


class TestFormLabelChecks(unittest.TestCase):
    def test_input_without_label_flagged(self):
        issues = check_form_inputs_missing_labels(soup_of('<input type="text" id="name">'))
        self.assertEqual(len(issues), 1)

    def test_input_with_matching_label_not_flagged(self):
        html = '<label for="name">Name</label><input type="text" id="name">'
        issues = check_form_inputs_missing_labels(soup_of(html))
        self.assertEqual(len(issues), 0)

    def test_input_wrapped_in_label_not_flagged(self):
        html = '<label>Name <input type="text"></label>'
        issues = check_form_inputs_missing_labels(soup_of(html))
        self.assertEqual(len(issues), 0)

    def test_input_with_aria_label_not_flagged(self):
        html = '<input type="text" aria-label="Search">'
        issues = check_form_inputs_missing_labels(soup_of(html))
        self.assertEqual(len(issues), 0)

    def test_hidden_input_not_flagged(self):
        html = '<input type="hidden" name="csrf_token">'
        issues = check_form_inputs_missing_labels(soup_of(html))
        self.assertEqual(len(issues), 0)

    def test_submit_button_not_flagged(self):
        html = '<input type="submit" value="Send">'
        issues = check_form_inputs_missing_labels(soup_of(html))
        self.assertEqual(len(issues), 0)


class TestHeadingHierarchy(unittest.TestCase):
    def test_no_headings_no_issues(self):
        issues = check_heading_hierarchy(soup_of("<p>No headings here</p>"))
        self.assertEqual(len(issues), 0)

    def test_proper_hierarchy_no_issues(self):
        html = "<h1>Title</h1><h2>Section</h2><h3>Subsection</h3>"
        issues = check_heading_hierarchy(soup_of(html))
        self.assertEqual(len(issues), 0)

    def test_starting_below_h1_flagged(self):
        html = "<h2>Title</h2>"
        issues = check_heading_hierarchy(soup_of(html))
        self.assertTrue(any(i.rule_id == "heading-no-h1" for i in issues))

    def test_skipped_level_flagged(self):
        html = "<h1>Title</h1><h3>Subsection</h3>"
        issues = check_heading_hierarchy(soup_of(html))
        self.assertTrue(any(i.rule_id == "heading-skipped-level" for i in issues))


class TestLinkChecks(unittest.TestCase):
    def test_vague_link_text_flagged(self):
        issues = check_vague_link_text(soup_of('<a href="/report">Click here</a>'))
        self.assertEqual(len(issues), 1)

    def test_descriptive_link_text_not_flagged(self):
        issues = check_vague_link_text(
            soup_of('<a href="/report">Download the 2025 annual report</a>')
        )
        self.assertEqual(len(issues), 0)

    def test_empty_link_flagged(self):
        issues = check_empty_links(soup_of('<a href="/page"></a>'))
        self.assertEqual(len(issues), 1)

    def test_link_with_aria_label_not_flagged_as_empty(self):
        html = '<a href="/page" aria-label="Go to homepage"></a>'
        issues = check_empty_links(soup_of(html))
        self.assertEqual(len(issues), 0)

    def test_link_with_img_alt_not_flagged_as_empty(self):
        html = '<a href="/page"><img src="logo.png" alt="Homepage"></a>'
        issues = check_empty_links(soup_of(html))
        self.assertEqual(len(issues), 0)


class TestLangAndTitle(unittest.TestCase):
    def test_missing_lang_flagged(self):
        issues = check_missing_lang_attribute(soup_of("<html><body></body></html>"))
        self.assertEqual(len(issues), 1)

    def test_present_lang_not_flagged(self):
        issues = check_missing_lang_attribute(soup_of('<html lang="en"><body></body></html>'))
        self.assertEqual(len(issues), 0)

    def test_missing_title_flagged(self):
        issues = check_missing_page_title(soup_of("<html><head></head></html>"))
        self.assertEqual(len(issues), 1)

    def test_empty_title_flagged(self):
        issues = check_missing_page_title(soup_of("<html><head><title></title></head></html>"))
        self.assertEqual(len(issues), 1)

    def test_present_title_not_flagged(self):
        html = "<html><head><title>My Page</title></head></html>"
        issues = check_missing_page_title(soup_of(html))
        self.assertEqual(len(issues), 0)


class TestTablesAndTabindex(unittest.TestCase):
    def test_table_without_th_flagged(self):
        html = "<table><tr><td>A</td><td>B</td></tr></table>"
        issues = check_tables_missing_headers(soup_of(html))
        self.assertEqual(len(issues), 1)

    def test_table_with_th_not_flagged(self):
        html = "<table><tr><th>A</th><th>B</th></tr></table>"
        issues = check_tables_missing_headers(soup_of(html))
        self.assertEqual(len(issues), 0)

    def test_positive_tabindex_flagged(self):
        issues = check_positive_tabindex(soup_of('<div tabindex="5"></div>'))
        self.assertEqual(len(issues), 1)

    def test_zero_tabindex_not_flagged(self):
        issues = check_positive_tabindex(soup_of('<div tabindex="0"></div>'))
        self.assertEqual(len(issues), 0)

    def test_negative_tabindex_not_flagged(self):
        issues = check_positive_tabindex(soup_of('<div tabindex="-1"></div>'))
        self.assertEqual(len(issues), 0)


if __name__ == "__main__":
    unittest.main()
