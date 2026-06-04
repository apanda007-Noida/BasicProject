import os
import json
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (Classifier) %(message)s",
    handlers=[
        logging.FileHandler("logs/classifier.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Configure Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    logging.warning("GEMINI_API_KEY is not set in environment. Intent classifier will fail-safe to 'ADVISORY'.")

SYSTEM_INSTRUCTION = """
You are a classification assistant. Your task is to classify user queries about mutual funds into either 'FACTUAL' or 'ADVISORY'.

- 'FACTUAL' queries are objective, asking for specific metrics, dates, names, or values (e.g. exit loads, expense ratios, NAV, AUM, managers, launch dates, holdings, process guidelines).
- 'ADVISORY' queries ask for opinions, comparisons, performance predictions, recommendations, suitability, or whether they should invest (e.g. 'Is this fund good?', 'Which is better?', 'Should I invest?', 'Will this give high returns?').

Format your response strictly as JSON with a single key 'intent' whose value is either 'FACTUAL' or 'ADVISORY'.
"""

def classify_query(query: str) -> str:
    """
    Classify the query intent using Gemini 1.5 Flash.
    Defaults to 'ADVISORY' as a security fail-safe on error.
    """
    if not API_KEY:
        logging.error("Gemini API key missing. Defaulting to 'ADVISORY' refusal.")
        return "ADVISORY"
        
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )
        
        prompt = f"""{SYSTEM_INSTRUCTION}

User Query: "{query}"
JSON Response:"""
        
        logging.info(f"Classifying query: '{query}'")
        response = model.generate_content(prompt)
        
        # Parse the JSON output
        result_dict = json.loads(response.text.strip())
        intent = result_dict.get("intent", "ADVISORY").upper()
        
        if intent not in ["FACTUAL", "ADVISORY"]:
            intent = "ADVISORY"
            
        logging.info(f"Classified intent: '{intent}'")
        return intent
        
    except Exception as e:
        logging.error(f"Error during query classification: {e}. Defaulting to 'ADVISORY'.")
        return "ADVISORY"

if __name__ == "__main__":
    # Test cases
    test_queries = [
        "What is the expense ratio of HDFC Small Cap Fund?",
        "Should I invest in HDFC Mid Cap Fund for retirement?",
        "Who is the manager of HDFC Defence Fund?",
        "Which mutual fund has the highest return in 5 years?",
        "How can I download capital gains statement?"
    ]
    
    print("=== Testing Intent Classifier ===")
    for q in test_queries:
        intent = classify_query(q)
        print(f"Query: '{q}' -> Intent: {intent}")
        print("-" * 30)
