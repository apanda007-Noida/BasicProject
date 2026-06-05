import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.security.pii_scrubber import scrub_pii
from src.guardrails.classifier import classify_query
from src.guardrails.refusal_handler import get_refusal_response
from src.guardrails.pipeline import process_query

class TestPIIScrubber(unittest.TestCase):
    def test_pan_redaction(self):
        query = "My PAN card is ABCDE1234F."
        self.assertEqual(scrub_pii(query), "My PAN card is [REDACTED_PAN].")

    def test_aadhaar_redaction(self):
        query_spaced = "My Aadhaar is 1234 5678 9012."
        query_flat = "Aadhaar number: 987654321098"
        self.assertEqual(scrub_pii(query_spaced), "My Aadhaar is [REDACTED_AADHAAR].")
        self.assertEqual(scrub_pii(query_flat), "Aadhaar number: [REDACTED_AADHAAR]")

    def test_email_redaction(self):
        query = "Contact me at user.test-123@sub.domain.com for queries."
        self.assertEqual(scrub_pii(query), "Contact me at [REDACTED_EMAIL] for queries.")

    def test_phone_redaction(self):
        query_simple = "Call me on 9876543210."
        query_prefix = "My phone is +91-8888888888."
        self.assertEqual(scrub_pii(query_simple), "Call me on [REDACTED_PHONE].")
        self.assertEqual(scrub_pii(query_prefix), "My phone is [REDACTED_PHONE].")

    def test_bank_account_redaction(self):
        query = "Send money to account 123456789012345."
        self.assertEqual(scrub_pii(query), "Send money to account [REDACTED_ACCOUNT].")

    def test_context_aware_otp_redaction(self):
        # With verification/OTP context, numbers should be redacted as OTP
        query_with_context = "My verification code is 58129."
        self.assertEqual(scrub_pii(query_with_context), "My verification code is [REDACTED_OTP].")
        
        # Without verification/OTP context, numbers should NOT be redacted as OTP
        query_without_context = "The minimum SIP amount is 1000 and the fund launched in 2013."
        # Confirm that 1000 and 2013 are NOT redacted
        self.assertNotIn("[REDACTED_OTP]", scrub_pii(query_without_context))
        self.assertIn("1000", scrub_pii(query_without_context))
        self.assertIn("2013", scrub_pii(query_without_context))


class TestIntentClassifier(unittest.TestCase):
    @patch("src.guardrails.classifier.client")
    def test_factual_query_classification_mock(self, mock_client):
        # Set up mock response for Groq model
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"intent": "FACTUAL"}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Run classification with patches in place
        with patch("src.guardrails.classifier.client", mock_client):
            intent = classify_query("What is the NAV of HDFC Small Cap Fund?")
            self.assertEqual(intent, "FACTUAL")

    @patch("src.guardrails.classifier.client")
    def test_advisory_query_classification_mock(self, mock_client):
        # Set up mock response for Groq model
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"intent": "ADVISORY"}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch("src.guardrails.classifier.client", mock_client):
            intent = classify_query("Should I buy HDFC Mid Cap Opportunities Fund?")
            self.assertEqual(intent, "ADVISORY")

    def test_classification_failsafe_no_key(self):
        # If client is unset/None, classify_query must return "ADVISORY"
        with patch("src.guardrails.classifier.client", None):
            intent = classify_query("What is the exit load of HDFC Small Cap?")
            self.assertEqual(intent, "ADVISORY")

    @patch("src.guardrails.classifier.client")
    def test_classification_failsafe_on_exception(self, mock_client):
        # If chat completion throws an exception, must fallback to "ADVISORY"
        mock_client.chat.completions.create.side_effect = Exception("API error")
        
        with patch("src.guardrails.classifier.client", mock_client):
            intent = classify_query("What is the exit load of HDFC Small Cap?")
            self.assertEqual(intent, "ADVISORY")


class TestRefusalHandler(unittest.TestCase):
    def test_refusal_contains_education_links(self):
        response = get_refusal_response()
        self.assertIn("https://www.amfiindia.com/", response)
        self.assertIn("https://www.sebi.gov.in/", response)
        self.assertIn("facts-only assistant", response)


class TestPipelineIntegration(unittest.TestCase):
    @patch("src.guardrails.pipeline.classify_query")
    def test_pipeline_advisory_flow(self, mock_classify):
        # Force classification to ADVISORY
        mock_classify.return_value = "ADVISORY"
        
        # Test pipeline execution
        query = "Should I invest my life savings in HDFC Small Cap?"
        result = process_query(query)
        
        self.assertEqual(result["intent"], "ADVISORY")
        self.assertTrue(result["response"].startswith("I am a facts-only assistant"))
        self.assertEqual(result["chunks"], [])

    @patch("src.guardrails.pipeline.generate_response")
    @patch("src.guardrails.pipeline.classify_query")
    def test_pipeline_factual_flow(self, mock_classify, mock_generate):
        # Force classification to FACTUAL
        mock_classify.return_value = "FACTUAL"
        mock_generate.return_value = "The exit load is 1.0%. [Source: https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth]"
        
        # Test pipeline execution
        query = "What is the exit load of HDFC Small Cap Fund?"
        result = process_query(query, k=1)
        
        self.assertEqual(result["intent"], "FACTUAL")
        self.assertIn("The exit load is 1.0%", result["response"])
        self.assertTrue(len(result["chunks"]) > 0)
        self.assertEqual(result["chunks"][0]["metadata"]["scheme_name"], "HDFC Small Cap Fund Direct Growth")

    @patch("src.guardrails.pipeline.classify_query")
    def test_pipeline_pii_scrubbing_before_retrieval(self, mock_classify):
        # Force classification to FACTUAL
        mock_classify.return_value = "FACTUAL"
        
        # Query containing sensitive PII and a scheme search term
        query = "My email is leak@test.com, tell me about HDFC Small Cap exit load."
        
        with patch("src.guardrails.pipeline.retrieve_relevant_chunks") as mock_retrieve:
            mock_retrieve.return_value = []
            process_query(query)
            
            # The retrieval engine should receive the scrubbed query, not the raw query
            called_query = mock_retrieve.call_args[0][0]
            self.assertNotIn("leak@test.com", called_query)
            self.assertIn("[REDACTED_EMAIL]", called_query)

if __name__ == "__main__":
    unittest.main()
