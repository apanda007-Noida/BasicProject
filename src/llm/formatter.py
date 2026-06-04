import re
import datetime
import logging

def sanitize_text(text: str) -> str:
    """Replace Unicode rupee symbol and clean up whitespace."""
    if not text:
        return ""
    # Replace Unicode rupee symbol \u20b9 with Rs.
    text = text.replace("\u20b9", "Rs.")
    return text.strip()

def extract_latest_date(chunks: list) -> str:
    """Extract and format the latest last_updated_date from chunk metadata as YYYY-MM-DD."""
    latest_dt = None
    for chunk in chunks:
        dt_str = chunk.get("metadata", {}).get("last_updated_date")
        if dt_str:
            try:
                # Handle ISO format like 2026-06-04T19:49:34Z
                dt = datetime.datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                if not latest_dt or dt > latest_dt:
                    latest_dt = dt
            except ValueError:
                # If date format varies, log warning and try parsing prefix
                logging.warning(f"Could not parse date string: {dt_str}")
                
    if latest_dt:
        return latest_dt.strftime("%Y-%m-%d")
    
    # Fallback to current date if metadata date is missing or invalid
    return datetime.datetime.utcnow().strftime("%Y-%m-%d")

def format_response(response_text: str, chunks: list) -> str:
    """Sanitize text and append the last updated date footer."""
    sanitized = sanitize_text(response_text)
    latest_date = extract_latest_date(chunks)
    footer = f"\n\nLast updated from sources: {latest_date}"
    return f"{sanitized}{footer}"

def count_sentences(text: str) -> int:
    """
    Count the number of sentences in the text, ignoring decimals, abbreviations, and citation links.
    """
    # Remove the footer if present to avoid counting it
    text_no_footer = re.split(r'\n\nLast updated from sources:', text)[0]
    
    # Strip citation links like [Source: URL] or raw URLs
    text_no_source = re.sub(r'\[?Source:\s*https?://[^\s)\]]+\]?', '', text_no_footer)
    text_no_url = re.sub(r'https?://[^\s)\]]+', '', text_no_source)
    
    # Replace decimal numbers (e.g. 0.73, 152.199) with placeholders
    text_no_decimals = re.sub(r'\b\d+\.\d+\b', 'NUM', text_no_url)
    
    # Replace common abbreviations followed by period
    text_no_abbrev = re.sub(r'\b(Rs|Mr|Ms|Mrs|Dr|Co|Ltd|Inc)\.', r'\1_TEMP', text_no_decimals)
    
    # Split by standard sentence terminal characters followed by whitespace or end of string
    sentences = re.split(r'[.!?]+(?=\s|$)', text_no_abbrev)
    
    # Filter out empty splits and splits containing only non-alphanumeric chars
    sentences = [s.strip() for s in sentences if s.strip() and re.search(r'[a-zA-Z0-9]', s)]
    return len(sentences)

def validate_compliance(full_response_text: str) -> dict:
    """
    Validate that the formatted response complies with all compliance constraints:
    1. Maximum of 3 sentences (excluding the last updated footer).
    2. Exactly one citation link.
    """
    # Extract URLs from the response
    urls = re.findall(r'https?://[^\s)\]]+', full_response_text)
    # Ignore AMFI/SEBI links if present in a refusal response (though pipeline bypasses LLM for refusals)
    urls_filtered = [u for u in urls if "amfiindia.com" not in u and "sebi.gov.in" not in u]
    
    # Count sentences
    sentence_count = count_sentences(full_response_text)
    
    # Rules compliance check
    sentence_ok = sentence_count <= 3
    citation_ok = len(urls_filtered) == 1
    
    is_compliant = sentence_ok and citation_ok
    
    errors = []
    if not sentence_ok:
        errors.append(f"Sentence count {sentence_count} exceeds maximum of 3 sentences.")
    if len(urls_filtered) != 1:
        errors.append(f"Expected exactly 1 citation URL, but found {len(urls_filtered)}.")

    return {
        "is_compliant": is_compliant,
        "sentence_count": sentence_count,
        "citation_count": len(urls_filtered),
        "errors": errors
    }

if __name__ == "__main__":
    # Test cases
    test_text = "The expense ratio is 0.73%. The NAV is Rs. 152.199. It is managed by Chirag. [Source: https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth]"
    chunks = [{"metadata": {"last_updated_date": "2026-06-04T19:49:34Z"}}]
    
    formatted = format_response(test_text, chunks)
    print("=== Formatted ===")
    print(formatted)
    
    compliance = validate_compliance(formatted)
    print("\n=== Compliance ===")
    print(compliance)
