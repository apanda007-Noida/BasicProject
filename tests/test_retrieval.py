import unittest
import os
import sys

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag.retriever import retrieve_relevant_chunks

class TestRetrievalEngine(unittest.TestCase):
    def test_small_cap_expense_ratio(self):
        query = "What is the expense ratio of HDFC Small Cap Fund?"
        results = retrieve_relevant_chunks(query, k=2)
        
        self.assertTrue(len(results) > 0, "No chunks returned for Small Cap query")
        
        # The top result should be the factual metrics chunk
        top_chunk = results[0]
        self.assertEqual(top_chunk["metadata"]["scheme_name"], "HDFC Small Cap Fund Direct Growth")
        self.assertIn("Section: Factual Scheme Metrics", top_chunk["text"])
        self.assertIn("Expense Ratio", top_chunk["text"])
        
    def test_mid_cap_fund_manager(self):
        query = "Who is the fund manager of HDFC Mid Cap Opportunities?"
        results = retrieve_relevant_chunks(query, k=2)
        
        self.assertTrue(len(results) > 0, "No chunks returned for Mid Cap query")
        
        top_chunk = results[0]
        self.assertEqual(top_chunk["metadata"]["scheme_name"], "HDFC Mid Cap Fund Direct Growth")
        self.assertIn("Section: Fund Management", top_chunk["text"])
        self.assertIn("Chirag Setalvad", top_chunk["text"])
        
    def test_defence_fund_holdings(self):
        query = "Show me the top holdings of HDFC Defence Fund"
        results = retrieve_relevant_chunks(query, k=2)
        
        self.assertTrue(len(results) > 0, "No chunks returned for Defence Fund query")
        
        top_chunk = results[0]
        self.assertEqual(top_chunk["metadata"]["scheme_name"], "HDFC Defence Fund Direct Growth")
        self.assertIn("Section: Top Portfolio Holdings", top_chunk["text"])
        
    def test_global_query_no_scheme(self):
        # A query that doesn't specify a scheme should perform a global search
        query = "what is the general tax impact on mutual funds?"
        results = retrieve_relevant_chunks(query, k=2)
        
        self.assertTrue(len(results) > 0, "No chunks returned for general query")
        # Ensure it didn't filter by a single scheme (should search globally)
        self.assertTrue(any("tax" in c["text"].lower() or "redeem" in c["text"].lower() for c in results))

if __name__ == "__main__":
    unittest.main()
