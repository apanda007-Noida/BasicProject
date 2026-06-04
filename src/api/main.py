import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from src.guardrails.pipeline import process_query

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (API) %(message)s",
    handlers=[
        logging.FileHandler("logs/api.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

app = FastAPI(
    title="Mutual Fund FAQ Assistant",
    description="A facts-only RAG assistant for HDFC Mutual Fund schemes."
)

class ChatRequest(BaseModel):
    message: str

# Config Endpoint
@app.get("/api/config")
def get_config():
    """Return welcome instructions, disclaimer, and clickable sample questions."""
    return {
        "welcome_message": (
            "Welcome! I am a facts-only assistant for HDFC Mutual Fund schemes. "
            "I can provide objective, official information regarding scheme metrics, expense ratios, "
            "exit loads, minimum SIPs, and fund management. Ask me a question below or choose one of the examples."
        ),
        "disclaimer": "Facts-only. No investment advice.",
        "example_questions": [
            "What is the expense ratio of HDFC Small Cap Fund?",
            "Who is the fund manager of HDFC Mid-Cap Opportunities?",
            "What exit load is applicable to HDFC Defence Fund?"
        ]
    }

# Chat Endpoint
@app.post("/api/chat")
def chat(request: ChatRequest):
    """Process query through guardrails, intent classifier, and retrieval/generation pipeline."""
    query = request.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query message cannot be empty.")
    
    try:
        logging.info(f"Received API query: '{query}'")
        result = process_query(query)
        return result
    except Exception as e:
        logging.error(f"Error processing API query: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing query.")

# Serve static frontend files
# Create public directory if it doesn't exist
os.makedirs("public", exist_ok=True)

# Mount the static files directory
app.mount("/static", StaticFiles(directory="public"), name="static")

# Serve index.html at root
@app.get("/")
def serve_index():
    index_path = os.path.join("public", "index.html")
    if not os.path.exists(index_path):
        # Create a basic index.html if it's missing to avoid 404
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("<h1>Mutual Fund FAQ Assistant is loading...</h1>")
    return FileResponse(index_path)
