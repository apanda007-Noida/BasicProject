import unittest
import os
import sys

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm.formatter import (
    sanitize_text,
    extract_latest_date,
    format_response,
    count_sentences,
    validate_compliance
)

class TestFormatter(unittest.TestCase):
    def test_rupee_sanitization(self):
        text = "The NAV of the fund is \u20b9150.50 and the minimum investment is \u20b91000."
        self.assertEqual(sanitize_text(text), "The NAV of the fund is Rs.150.50 and the minimum investment is Rs.1000.")

    def test_extract_latest_date_single(self):
        chunks = [
            {"metadata": {"last_updated_date": "2026-06-04T12:00:00Z"}},
        ]
        self.assertEqual(extract_latest_date(chunks), "2026-06-04")

    def test_extract_latest_date_multiple(self):
        chunks = [
            {"metadata": {"last_updated_date": "2026-06-02T10:00:00Z"}},
            {"metadata": {"last_updated_date": "2026-06-05T14:30:00Z"}},
            {"metadata": {"last_updated_date": "2026-06-04T19:00:00Z"}},
        ]
        self.assertEqual(extract_latest_date(chunks), "2026-06-05")

    def test_format_response_appends_footer(self):
        response_text = "HDFC Small Cap Fund has an expense ratio of 0.73%."
        chunks = [{"metadata": {"last_updated_date": "2026-06-04T19:49:34Z"}}]
        formatted = format_response(response_text, chunks)
        
        expected = "HDFC Small Cap Fund has an expense ratio of 0.73%.\n\nLast updated from sources: 2026-06-04"
        self.assertEqual(formatted, expected)

    def test_sentence_counter_decimals_and_abbrev(self):
        # A test string containing abbreviations and decimal numbers
        text = "The expense ratio is 0.73%. The NAV is Rs. 152.199. It is managed by Chirag."
        self.assertEqual(count_sentences(text), 3)

    def test_sentence_counter_with_footer(self):
        # Decimals, abbreviations, and a footer
        text = "The exit load is 1.0% if redeemed before 1 year. No exit load applies after that. Refer to [Source: https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth].\n\nLast updated from sources: 2026-06-04"
        self.assertEqual(count_sentences(text), 3)

    def test_compliance_valid(self):
        text = "The minimum SIP is Rs. 100. The exit load is 1.0%. [Source: https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth]\n\nLast updated from sources: 2026-06-04"
        comp = validate_compliance(text)
        self.assertTrue(comp["is_compliant"])
        self.assertEqual(comp["sentence_count"], 2)
        self.assertEqual(comp["citation_count"], 1)

    def test_compliance_too_many_sentences(self):
        text = "Sentence one. Sentence two. Sentence three. Sentence four. [Source: https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth]\n\nLast updated from sources: 2026-06-04"
        comp = validate_compliance(text)
        self.assertFalse(comp["is_compliant"])
        self.assertIn("exceeds maximum of 3 sentences", comp["errors"][0])

    def test_compliance_missing_citation(self):
        text = "The expense ratio is 0.73%.\n\nLast updated from sources: 2026-06-04"
        comp = validate_compliance(text)
        self.assertFalse(comp["is_compliant"])
        self.assertIn("Expected exactly 1 citation URL", comp["errors"][0])

    def test_compliance_multiple_citations(self):
        text = "Visit https://groww.in/mutual-funds/1 and also https://groww.in/mutual-funds/2.\n\nLast updated from sources: 2026-06-04"
        comp = validate_compliance(text)
        self.assertFalse(comp["is_compliant"])
        self.assertIn("Expected exactly 1 citation URL", comp["errors"][0])

if __name__ == "__main__":
    unittest.main()
