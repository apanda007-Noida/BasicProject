import os
import re
import logging
import datetime
from sentence_transformers import SentenceTransformer
import chromadb

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (Indexer) %(message)s",
    handlers=[
        logging.FileHandler("logs/indexer.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

INGESTED_DIR = "data/ingested"
CHROMA_DIR = "data/chroma"
COLLECTION_NAME = "mutual_funds"

def parse_metadata(content):
    """Extract source URL and ingestion date from metadata section."""
    source_url = "https://groww.in"
    scraped_at = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    url_match = re.search(r"-\s+\*\*Source URL\*\*:\s+([^\n]+)", content)
    if url_match:
        source_url = url_match.group(1).strip()
        
    date_match = re.search(r"-\s+\*\*Scraped At\*\*:\s+([^\n]+)", content)
    if date_match:
        scraped_at = date_match.group(1).strip()
        
    return source_url, scraped_at

def chunk_markdown_file(filepath):
    """Parse a scheme markdown file and split it into sections."""
    filename = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Get metadata
    source_url, scraped_at = parse_metadata(content)
    
    # Extract Scheme Name
    scheme_name = "HDFC Mutual Fund"
    scheme_match = re.match(r"#\s+([^\n]+)", content)
    if scheme_match:
        scheme_name = scheme_match.group(1).strip()
        
    # If it is the filter list, chunk by rows in the table
    if filename == "hdfc-mutual-funds-filter-list.md":
        logging.info(f"Chunking filter list file: {filename}")
        chunks = []
        table_started = False
        row_id = 0
        for line in content.split("\n"):
            line = line.strip()
            # Detect table headers
            if "| Scheme Name |" in line:
                table_started = True
                continue
            if table_started and line.startswith("|") and not line.startswith("| :---"):
                parts = [p.strip() for p in line.split("|")[1:-1]]
                if len(parts) >= 6 and parts[0] != "Scheme Name":
                    row_id += 1
                    row_text = (
                        f"Fund: {parts[0]}\n"
                        f"Category: {parts[1]}\n"
                        f"Risk: {parts[2]}\n"
                        f"NAV: {parts[3]}\n"
                        f"AUM (Cr): {parts[4]}\n"
                        f"Expense Ratio: {parts[5]}"
                    )
                    if len(parts) > 6:
                        row_text += f"\nExit Load: {parts[6]}"
                        
                    chunk_text = (
                        f"Fund House: HDFC Mutual Fund\n"
                        f"Section: Filter List Summary Row\n"
                        f"---\n"
                        f"{row_text}"
                    )
                    
                    metadata = {
                        "source_url": source_url,
                        "scheme_name": parts[0],
                        "last_updated_date": scraped_at,
                        "section_name": "Filter List Row"
                    }
                    
                    chunk_id = f"filter-list-row-{row_id}"
                    chunks.append((chunk_id, chunk_text, metadata))
        return chunks

    # For standard scheme documents, split by level 2 headings (##)
    sections = re.split(r"\n##\s+", content)
    # The first section is the header and overview before any '##'
    first_sec = sections[0].strip()
    
    # We will ignore the top-level '# ' header as its own chunk, but parse sections:
    chunks = []
    chunk_index = 0
    
    for sec in sections[1:]:
        sec = sec.strip()
        if not sec:
            continue
            
        # Separate title from body
        lines = sec.split("\n", 1)
        heading_title = lines[0].strip()
        body_content = lines[1].strip() if len(lines) > 1 else ""
        
        # Skip Ingestion Metadata section as its own chunk (we attach it to metadata instead)
        if heading_title == "Ingestion Metadata":
            continue
            
        # Prep text with parent context
        chunk_text = (
            f"Fund: {scheme_name}\n"
            f"Section: {heading_title}\n"
            f"---\n"
            f"{body_content}"
        )
        
        metadata = {
            "source_url": source_url,
            "scheme_name": scheme_name,
            "last_updated_date": scraped_at,
            "section_name": heading_title
        }
        
        # Clean slug for ID
        slug = re.sub(r"[^a-z0-9]+", "-", scheme_name.lower()).strip("-")
        heading_slug = re.sub(r"[^a-z0-9]+", "-", heading_title.lower()).strip("-")
        chunk_id = f"{slug}-{heading_slug}"
        
        chunks.append((chunk_id, chunk_text, metadata))
        
    return chunks

def build_index():
    logging.info("Starting ChromaDB Indexing Process")
    
    if not os.path.exists(INGESTED_DIR):
        logging.error(f"Ingested files directory '{INGESTED_DIR}' does not exist. Run scraper first.")
        return False
        
    # 1. Initialize local BGE embedding model
    logging.info("Loading local BGE embedding model 'BAAI/bge-small-en-v1.5'...")
    model = SentenceTransformer('BAAI/bge-small-en-v1.5')
    
    # 2. Initialize Chroma persistent client
    logging.info(f"Connecting to ChromaDB persisted at: {CHROMA_DIR}")
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    # 3. Create collection
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
    
    # Read files and generate chunks
    all_ids = []
    all_texts = []
    all_metadatas = []
    
    for filename in os.listdir(INGESTED_DIR):
        if filename.endswith(".md"):
            filepath = os.path.join(INGESTED_DIR, filename)
            try:
                chunks = chunk_markdown_file(filepath)
                for chunk_id, text, metadata in chunks:
                    all_ids.append(chunk_id)
                    all_texts.append(text)
                    all_metadatas.append(metadata)
            except Exception as e:
                logging.error(f"Error parsing file {filename}: {e}")
                
    if not all_texts:
        logging.warning("No chunks found to index.")
        return False
        
    logging.info(f"Generated {len(all_texts)} chunks from ingested documents.")
    
    # 4. Generate embeddings locally
    logging.info("Generating BGE embeddings locally (this might take a moment on first run)...")
    # BGE models work best with a query prefix if doing queries, but for document ingestion 
    # we just encode the raw texts.
    embeddings = model.encode(all_texts, show_progress_bar=True).tolist()
    
    # 5. Load into ChromaDB
    logging.info(f"Uploading {len(all_texts)} documents to Chroma collection '{COLLECTION_NAME}'...")
    
    # Clear existing entries in the collection first to avoid duplicate keys / stale data
    existing_ids = collection.get()["ids"]
    if existing_ids:
        logging.info(f"Removing {len(existing_ids)} existing entries from collection...")
        collection.delete(ids=existing_ids)
        
    # Batch uploads if corpus grows, but for 90-100 chunks a single upload is perfectly fine
    collection.add(
        ids=all_ids,
        embeddings=embeddings,
        metadatas=all_metadatas,
        documents=all_texts
    )
    
    logging.info("Indexing completed successfully!")
    return True

if __name__ == "__main__":
    build_index()
