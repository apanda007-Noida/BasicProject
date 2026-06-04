import os
import re
import logging
from sentence_transformers import SentenceTransformer
import chromadb

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (Retriever) %(message)s",
    handlers=[
        logging.FileHandler("logs/retriever.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

CHROMA_DIR = "data/chroma"
COLLECTION_NAME = "mutual_funds"

# Curated list of exact scheme names mapped to regex match terms
SCHEME_PATTERNS = {
    "HDFC Mid Cap Fund Direct Growth": [r"mid\s*cap", r"mid-cap"],
    "HDFC Small Cap Fund Direct Growth": [r"small\s*cap", r"small-cap"],
    "HDFC Gold ETF Fund of Fund Direct Plan Growth": [r"gold\s*etf", r"gold\s*fund"],
    "HDFC Flexi Cap Direct Plan Growth": [r"flexi\s*cap", r"flexi-cap", r"equity\s*fund"],
    "HDFC Defence Fund Direct Growth": [r"defence", r"defense"],
    "HDFC NIFTY 50 Index Fund Direct Growth": [r"nifty\s*50", r"nifty-50", r"nifty\s*fifty"],
    "HDFC Large and Mid Cap Fund Direct Growth": [r"large\s*(and|&)\s*mid", r"large-and-mid"],
    "HDFC Infrastructure Fund Direct Growth": [r"infrastructure", r"infra"],
    "HDFC Banking & Financial Services Fund Direct Growth": [r"banking", r"financial\s*services"],
    "HDFC Innovation Fund Direct Growth": [r"innovation"],
    "HDFC Hybrid Equity Fund Direct Plan Growth": [r"hybrid\s*equity", r"premier\s*multi\s*cap", r"multi\s*cap", r"multi-cap"],
    "HDFC Diversified Equity All Cap Active FoF Direct Growth": [r"diversified\s*equity", r"all\s*cap\s*active", r"active\s*fof"],
    "HDFC Nifty LargeMidcap 250 Index Fund Direct Growth": [r"nifty\s*largemidcap\s*250", r"largemidcap\s*250", r"large\s*mid\s*250"],
    "HDFC BSE India Sector Leaders Index Fund Direct Growth": [r"bse\s*india", r"sector\s*leaders", r"india\s*sector\s*leaders"]
}

class RetrievalEngine:
    def __init__(self):
        logging.info("Initializing Retrieval Engine...")
        self.model = SentenceTransformer('BAAI/bge-small-en-v1.5')
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.collection = self.chroma_client.get_collection(name=COLLECTION_NAME)
        logging.info("Retrieval Engine initialized successfully.")

    def match_scheme_name(self, query):
        """Analyze query to see if it targets one of our 14 HDFC funds."""
        query_lower = query.lower()
        for scheme_name, patterns in SCHEME_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    logging.info(f"Query matched scheme filter: '{scheme_name}' (matched pattern: '{pattern}')")
                    return scheme_name
        logging.info("Query did not match any specific scheme filter. Performing global search.")
        return None

    def retrieve_relevant_chunks(self, query, k=3, distance_threshold=1.0):
        """Retrieve the top k relevant chunks, applying metadata filters and thresholds."""
        # 1. Check for targeted scheme name
        matched_scheme = self.match_scheme_name(query)
        
        # 2. Format query with BGE search prefix
        # BGE models recommend this prefix for optimal search retrieval performance
        prefixed_query = f"Represent this sentence for searching relevant passages: {query}"
        
        # 3. Embed the query
        query_embedding = self.model.encode(prefixed_query).tolist()
        
        # 4. Build query arguments
        query_args = {
            "query_embeddings": [query_embedding],
            "n_results": k
        }
        
        if matched_scheme:
            query_args["where"] = {"scheme_name": matched_scheme}
            
        # 5. Query ChromaDB
        results = self.collection.query(**query_args)
        
        # 6. Format and threshold results
        formatted_results = []
        
        if not results or not results["documents"] or not results["documents"][0]:
            return formatted_results
            
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]
        ids = results["ids"][0]
        
        for i in range(len(documents)):
            distance = distances[i]
            # Chroma returns L2 distance (squared). For cosine similarity distance is 1 - similarity.
            # BGE-small embeddings are normalized, so L2 distance directly maps to cosine distance.
            # Lower distance means higher similarity.
            if distance > distance_threshold:
                logging.warning(f"Chunk '{ids[i]}' filtered out due to distance {distance:.4f} > threshold {distance_threshold}")
                continue
                
            formatted_results.append({
                "id": ids[i],
                "text": documents[i],
                "metadata": metadatas[i],
                "distance": distance
            })
            logging.info(f"Retrieved chunk '{ids[i]}' (distance: {distance:.4f})")
            
        return formatted_results

# Singleton instance
_engine = None

def get_retrieval_engine():
    global _engine
    if _engine is None:
        _engine = RetrievalEngine()
    return _engine

def retrieve_relevant_chunks(query, k=3, distance_threshold=1.0):
    """Module level helper function to trigger retrieval."""
    engine = get_retrieval_engine()
    return engine.retrieve_relevant_chunks(query, k, distance_threshold)

if __name__ == "__main__":
    # Test execution
    test_query = "What is the expense ratio of HDFC Small Cap Fund?"
    print(f"\n--- Testing Retrieval for: '{test_query}' ---")
    chunks = retrieve_relevant_chunks(test_query, k=3)
    for c in chunks:
        print(f"\n[ID]: {c['id']} (Distance: {c['distance']:.4f})")
        print(f"[URL]: {c['metadata']['source_url']}")
        text_clean = c['text'][:200].replace("\u20b9", "Rs.")
        print(f"[Text Snippet]:\n{text_clean}...")
