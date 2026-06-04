import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm.client import generate_response

class TestLLMGeneration(unittest.TestCase):
    @patch("src.llm.client.client")
    def test_generation_success_mock(self, mock_client):
        # Mock client chat completions response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="The expense ratio is 0.73%. [Source: https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth]"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        
        chunks = [
            {
                "text": "Fund: HDFC Small Cap Fund Direct Growth\nSection: Factual Scheme Metrics\n---\nExpense Ratio: 0.73%",
                "metadata": {
                    "source_url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth"
                }
            }
        ]
        
        # Patch client to not be None
        with patch("src.llm.client.client", mock_client):
            response = generate_response("What is the expense ratio?", chunks)
            self.assertEqual(response, "The expense ratio is 0.73%. [Source: https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth]")
            
            # Verify completions was called with Llama 3.1 model
            args, kwargs = mock_client.chat.completions.create.call_args
            self.assertEqual(kwargs["model"], "llama-3.1-8b-instant")
            self.assertEqual(kwargs["temperature"], 0.0)

    def test_generation_failsafe_no_key(self):
        # Force client to be None (key missing)
        with patch("src.llm.client.client", None):
            chunks = [{"text": "Dummy text", "metadata": {"source_url": "http://groww.in"}}]
            response = generate_response("What is the NAV?", chunks)
            self.assertEqual(response, "Factual information service is temporarily unavailable. Please refer to official AMC sources.")

    @patch("src.llm.client.client")
    def test_generation_failsafe_on_exception(self, mock_client):
        # Force chat completion call to raise an exception
        mock_client.chat.completions.create.side_effect = Exception("API rate limit exceeded")
        
        chunks = [{"text": "Dummy text", "metadata": {"source_url": "http://groww.in"}}]
        with patch("src.llm.client.client", mock_client):
            response = generate_response("What is the NAV?", chunks)
            self.assertEqual(response, "Factual information service is temporarily unavailable. Please refer to official AMC sources.")

    @patch("src.llm.client.client")
    def test_generation_empty_chunks(self, mock_client):
        # Empty chunks should trigger immediate fallback text
        with patch("src.llm.client.client", mock_client):
            response = generate_response("What is the NAV?", [])
            self.assertEqual(response, "Factual information regarding this query is not available in the official sources.")

if __name__ == "__main__":
    unittest.main()
