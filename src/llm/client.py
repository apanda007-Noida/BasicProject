import os
import logging
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (LLMClient) %(message)s",
    handlers=[
        logging.FileHandler("logs/llm_client.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "llama-3.1-8b-instant"

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    logging.warning("GROQ_API_KEY is not set in environment. LLM generation will fallback to default message.")
    client = None

SYSTEM_PROMPT = """You are a facts-only mutual fund FAQ assistant. Your job is to answer user queries strictly using the provided context chunks.

Core Compliance Constraints:
1. Facts only. Never suggest, recommend, compare, buy/sell, or offer any form of investment advice.
2. Keep the response extremely concise. You must not exceed 3 sentences.
3. If the provided context does not contain enough information to answer the query, state: "Factual information regarding this query is not available in the official sources."
4. You must include exactly one citation link referencing the source URL from the provided context at the end of your response text (e.g. "... [Source: https://groww.in/mutual-funds/...]").
5. Do not extrapolate, speculate, or introduce external facts.
"""

def generate_response(query: str, chunks: list) -> str:
    """
    Generate a response to the query using Groq API and llama-3.1-8b-instant.
    Uses context chunks to synthesize a factual response.
    """
    fallback_message = "Factual information service is temporarily unavailable. Please refer to official AMC sources."

    if not client:
        logging.error("Groq client not initialized (missing API key). Returning fallback.")
        return fallback_message

    if not chunks:
        logging.warning("No context chunks provided for generation. Returning fallback message.")
        return "Factual information regarding this query is not available in the official sources."

    # Format context chunks
    context_str = ""
    for idx, chunk in enumerate(chunks, 1):
        text = chunk.get("text", "")
        url = chunk.get("metadata", {}).get("source_url", "https://groww.in")
        context_str += f"--- Chunk {idx} ---\nContent:\n{text}\nSource URL: {url}\n\n"

    try:
        user_content = f"Context:\n{context_str}\nUser Query: {query}\nResponse:"
        
        logging.info(f"Sending request to Groq model {MODEL_NAME}...")
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            model=MODEL_NAME,
            temperature=0.0  # Keep response deterministic and highly factual
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        logging.info("Groq response generated successfully.")
        return response_text

    except Exception as e:
        logging.error(f"Error during Groq generation: {e}. Returning fallback message.")
        return fallback_message

if __name__ == "__main__":
    # Test execution with dummy chunk
    dummy_chunks = [
        {
            "text": "Fund: HDFC Small Cap Fund Direct Growth\nSection: Factual Scheme Metrics\n---\nNAV (As of 04-Jun-2026): Rs. 152.199\nExpense Ratio: 0.73%\nAUM: Rs. 38,168 Cr",
            "metadata": {
                "source_url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth"
            }
        }
    ]
    print("=== Testing LLM Generation ===")
    res = generate_response("What is the expense ratio of HDFC Small Cap Fund?", dummy_chunks)
    print(f"Response:\n{res}")
