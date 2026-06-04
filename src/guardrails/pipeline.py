import logging
import os
from src.security.pii_scrubber import scrub_pii
from src.guardrails.classifier import classify_query
from src.guardrails.refusal_handler import get_refusal_response
from src.rag.retriever import retrieve_relevant_chunks
from src.llm.client import generate_response
from src.llm.formatter import format_response, validate_compliance

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (Pipeline) %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def process_query(query: str, k: int = 3, distance_threshold: float = 1.0) -> dict:
    """
    Orchestrate query processing for the Mutual Fund FAQ Assistant:
    1. Scrub PII from the raw user query.
    2. Classify intent of the scrubbed query (FACTUAL vs ADVISORY).
    3. Retrieve relevant chunks from the vector store if FACTUAL,
       otherwise return standard educational refusal message immediately.
    4. Generate and format response using Groq if factual.
    """
    logging.info(f"Processing query: '{query}'")
    
    # Step 1: PII Scrubbing
    scrubbed_query = scrub_pii(query)
    if scrubbed_query != query:
        logging.info(f"Query PII scrubbed: '{scrubbed_query}'")
        
    # Step 2: Intent Classification
    intent = classify_query(scrubbed_query)
    logging.info(f"Intent classified: '{intent}'")
    
    # Step 3: Branching logic based on intent
    if intent == "ADVISORY":
        logging.info("Advisory query intercepted. Returning refusal response.")
        return {
            "intent": "ADVISORY",
            "response": get_refusal_response(),
            "chunks": []
        }
        
    # Factual branch
    logging.info("Factual query recognized. Performing retriever search...")
    try:
        chunks = retrieve_relevant_chunks(scrubbed_query, k=k, distance_threshold=distance_threshold)
        logging.info(f"Retrieved {len(chunks)} relevant chunks from vector database.")
        
        if not chunks:
            logging.warning("No relevant chunks found under distance threshold.")
            return {
                "intent": "FACTUAL",
                "response": "Factual information regarding this query is not available in the official sources.",
                "chunks": []
            }
            
        # Step 4: Generation & Formatting
        raw_response = generate_response(scrubbed_query, chunks)
        formatted_response = format_response(raw_response, chunks)
        
        # Log compliance check results
        compliance = validate_compliance(formatted_response)
        if not compliance["is_compliant"]:
            logging.warning(f"Generated response is non-compliant: {compliance['errors']}")
            
        return {
            "intent": "FACTUAL",
            "response": formatted_response,
            "chunks": chunks
        }
    except Exception as e:
        logging.error(f"Error during retrieval or generation: {e}. Falling back to advisory refusal for security.")
        return {
            "intent": "ADVISORY",
            "response": get_refusal_response(),
            "chunks": []
        }

if __name__ == "__main__":
    # Quick manual testing
    test_queries = [
        "What is the expense ratio of HDFC Small Cap Fund?",
        "Should I invest in HDFC Mid Cap Opportunities Fund?",
        "My email is customer@test.com, help me retrieve details on HDFC Defence Fund",
    ]
    
    print("\n=== Testing Query Pipeline ===")
    for q in test_queries:
        res = process_query(q)
        print(f"\nQuery: {q}")
        print(f"Result: {res}")
        print("-" * 50)
