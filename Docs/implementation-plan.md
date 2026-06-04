# Phase-Wise Implementation Plan: Mutual Fund FAQ Assistant

This implementation plan outlines the steps required to build the facts-only Mutual Fund FAQ Assistant using a Retrieval-Augmented Generation (RAG) approach based on the system architecture.

---

## Phase 1: Environment Setup & Data Ingestion
**Goal**: Establish the repository structure, prepare dependencies, and build the scheduler-driven web scraping pipeline.

### Steps
1.  **Project Initialization**:
    *   Set up a clean Python environment (Python 3.10+ recommended).
    *   Initialize virtual environment (`venv`) and create `requirements.txt` with core libraries:
        *   `google-generativeai` (for Gemini Flash & Embeddings)
        *   `chromadb` or `faiss-cpu` (for vector storage)
        *   `beautifulsoup4` and `requests` (for web scraping)
        *   `schedule` or `APScheduler` (for scheduling daily ingestion)
        *   `fastapi` & `uvicorn` (for the backend API)
        *   `python-dotenv` (for API key configuration)
2.  **Web Scraper Component**:
    *   Build a parser in `src/ingestion/scraper.py` targeting the 15 specified HDFC Mutual Fund URLs from Groww.
    *   Extract scheme names, expense ratios, exit loads, riskometers, benchmark indices, fund managers, and transaction details.
    *   Sanitize the scraped text to remove HTML boilerplate, header menus, footer links, and interactive widgets.
3.  **Daily Ingestion Scheduler**:
    *   Develop `src/ingestion/scheduler.py` using Python's `schedule` library.
    *   Configure the script to run continuously as a background service.
    *   Schedule it to run **daily at 10:00 AM IST** (04:30 AM UTC) to trigger the scraper, refresh the data, and update the vector database.

---

## Phase 2: RAG Pipeline - Indexing & Retrieval (Finalized Retrieval Strategy)
**Goal**: Implement document chunking, generate embeddings, and build the vector search retrieval component.

### Steps
1.  **Chunking & Processing**:
    *   Implement chunking logic in `src/rag/indexer.py` using a customized markdown parsing to split by section headers (`##`) to keep tables and lists cohesive, and split the filter list by table rows.
    *   Prepend parent context (fund name and section name) to each chunk to preserve query context.
    *   Attach metadata to each chunk: `source_url`, `scheme_name`, `last_updated_date`, and `section_name`.
2.  **Vector Store Setup**:
    *   Initialize a local persistent vector database using ChromaDB in `data/chroma`.
    *   Integrate local `BAAI/bge-small-en-v1.5` sentence-transformers model to run embeddings locally.
    *   Index all parsed mutual fund documents in the vector store.
3.  **Retriever Integration**:
    *   Implement retrieval engine in `src/rag/retriever.py` with the following decided strategy:
        *   **Query-to-Scheme Mapping**: Map queries to specific schemes using regex keyword pattern matching.
        *   **Metadata Filter**: If matched, query ChromaDB with `where={"scheme_name": matched_scheme_name}`. Otherwise, search globally.
        *   **BGE Search Query Prefix**: Prepend `"Represent this sentence for searching relevant passages: {query}"`.
        *   **Distance Thresholding**: Filter out chunks with L2 distance > 1.0.

---

## Phase 3: Guardrails, Security & Refusal Classifier
**Goal**: Secure the application against PII leaks and intercept advisory or opinion-based questions.

### Steps
1.  **PII Scrubbing Middleware**:
    *   Implement regex filters in `src/security/pii_scrubber.py` targeting PAN, Aadhaar, Email, Phone, bank account, and context-aware OTPs (only redact 4-6 digit numbers when verification/OTP keywords are in the query).
2.  **Intent & Advisory Classifier**:
    *   Implement `src/guardrails/classifier.py` using Gemini 1.5 Flash in JSON mode to classify queries into `FACTUAL` or `ADVISORY`.
    *   Implement fail-safe logic defaulting to `ADVISORY` on error.
3.  **Refusal Response Handler**:
    *   Implement `src/guardrails/refusal_handler.py` to return the polite SEBI/AMFI disclaimer.
4.  **Query Processing Pipeline**:
    *   Implement `src/guardrails/pipeline.py` to orchestrate: `scrub_pii(query)` -> `classify_query(query)` -> (if ADVISORY, return refusal; if FACTUAL, retrieve chunks).

---

## Phase 4: Generation & Compliance Engine
**Goal**: Set up Groq LLM integration, engineer system prompts, and validate formatting constraints.

### Steps
1.  **Groq API Client**:
    *   Establish integration with Groq API in `src/llm/client.py` using `groq` SDK.
    *   Configure connection to the `llama-3.1-8b-instant` model.
    *   Read `GROQ_API_KEY` from `.env`. Implement fail-safe fallback message if API key is missing or call fails.
2.  **System Prompt Design**:
    *   Write a robust system instruction enforcing the following rules:
        *   Answer queries strictly using the provided context chunks.
        *   Provide facts-only information; never recommend, suggest, or compare funds.
        *   If the context doesn't contain the answer, politely state that the information is unavailable in official sources.
        *   Keep responses within a **maximum of 3 sentences**.
        *   Include exactly **one citation link** referencing the source URL from metadata.
3.  **Output Formatter & Validator**:
    *   Structure the model response output in `src/llm/formatter.py` to ensure it appends the footer:
        `Last updated from sources: <YYYY-MM-DD>` (extracted and formatted from metadata).
    *   Add a post-generation checker to verify length (<= 3 sentences) and the presence of exactly one source link.
    *   Sanitize the output by replacing Unicode rupee symbols (`\u20b9`) with `Rs.`.

---

## Phase 5: Backend API & User Interface
**Goal**: Build the API layer and design a premium, responsive single-page web interface.

### Steps
1.  **FastAPI Backend Server**:
    *   Create `src/api/main.py` containing endpoints:
        *   `GET /api/config`: Returns configurations, welcome messages, and the 3 example questions.
        *   `POST /api/chat`: Takes the user query, processes it through guardrails/RAG, and returns the formatted response.
2.  **Frontend Interface**:
    *   Design a premium web page in `public/index.html` and `public/style.css` (using clean dark mode, responsive layout, modern typography, glassmorphism, and subtle micro-animations).
    *   Features:
        *   Welcome message & introduction.
        *   Three clickable example questions (e.g., *"What is the expense ratio of HDFC Small Cap Fund?"*).
        *   A prominent, sticky disclaimer banner: `Facts-only. No investment advice.`
        *   Clean, interactive chat history container showing citations and footers styled beautifully.

---

## Phase 6: Testing & Quality Assurance
**Goal**: Validate compliance, accuracy, and response formatting constraints.

### Steps
1.  **Test Suite Creation**:
    *   Write tests in `tests/test_guardrails.py` to ensure that advisory queries (like *"Should I invest in HDFC Mid-Cap?"*) are correctly refused.
    *   Write tests in `tests/test_formatter.py` to check that responses strictly respect the 3-sentence limit, single citation rule, and last updated footer.
2.  **Verification**:
    *   Verify the scraping pipeline operates without errors.
    *   Validate the daily scheduler fires correctly at 10:00 AM IST.
