import os
import json
import logging
import datetime
import urllib.parse
from bs4 import BeautifulSoup
import requests

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/scraper.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Core Groww URLs to scrape
URLS = [
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-nifty-50-index-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-large-and-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-infrastructure-fund-direct-growth",
    "https://groww.in/mutual-funds/filter?fund_house=%5B%22HDFC+Mutual+Fund%22%5D",
    "https://groww.in/mutual-funds/hdfc-banking-financial-services-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-innovation-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-premier-multi-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-diversified-equity-all-cap-active-fof-direct-growth",
    "https://groww.in/mutual-funds/hdfc-nifty-largemidcap-250-index-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-bse-india-sector-leaders-index-fund-direct-growth"
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

OUTPUT_DIR = "data/ingested"

def get_slug(url):
    """Generate a clean slug name for a URL."""
    parsed = urllib.parse.urlparse(url)
    if "filter" in parsed.path:
        return "hdfc-mutual-funds-filter-list"
    # Extract path segment (e.g. /mutual-funds/hdfc-mid-cap-fund-direct-growth)
    parts = parsed.path.strip("/").split("/")
    return parts[-1] if parts else "scraped-page"

def scrape_url(url, session):
    """Scrape a URL and return a dict of parsed metadata and Markdown output."""
    logging.info(f"Fetching URL: {url}")
    try:
        response = session.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to fetch {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    
    scraped_at = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    if not script:
        logging.warning(f"No Next.js payload found in {url}. Falling back to plain text extraction.")
        # Fallback raw text parsing
        main_content = soup.find(class_="layout-main") or soup.find(id="root") or soup.body
        body_text = main_content.get_text(separator="\n") if main_content else soup.get_text(separator="\n")
        lines = [line.strip() for line in body_text.split("\n") if line.strip()]
        sanitized_text = "\n".join(lines)
        
        markdown = f"""# Scraped Page: {url}

## Raw Content Fallback
{sanitized_text}

## Ingestion Metadata
- **Source URL**: {url}
- **Scraped At**: {scraped_at}
"""
        return {"type": "fallback", "markdown": markdown, "name": get_slug(url)}
        
    try:
        data = json.loads(script.string)
        page_props = data.get("props", {}).get("pageProps", {})
        
        # Detail Page Ingestion
        if "mfServerSideData" in page_props:
            mf_data = page_props["mfServerSideData"]
            scheme_name = mf_data.get("scheme_name", get_slug(url).replace("-", " ").title())
            logging.info(f"Parsing scheme detail page: {scheme_name}")
            
            # Format Lock-in
            lock_in = mf_data.get("lock_in", {})
            lock_in_str = "None"
            if isinstance(lock_in, dict) and any(lock_in.values()):
                lock_in_str = f"{lock_in.get('years', 0)} years, {lock_in.get('months', 0)} months, {lock_in.get('days', 0)} days"
            
            # Format Risk Rating / Classification
            risk = "N/A"
            if "return_stats" in mf_data and isinstance(mf_data["return_stats"], list) and len(mf_data["return_stats"]) > 0:
                risk = mf_data["return_stats"][0].get("risk") or mf_data["return_stats"][0].get("risk_rating") or "N/A"
            if not risk or risk == "N/A":
                risk = mf_data.get("risk") or mf_data.get("nfo_risk") or "N/A"
            
            # Format Fund Managers
            managers = []
            mgr_details_block = []
            for mgr in mf_data.get("fund_manager_details", []):
                name = mgr.get("person_name", "N/A")
                managers.append(name)
                edu = mgr.get("education", "N/A")
                exp = mgr.get("experience", "N/A")
                other_funds = mgr.get("funds_managed", "N/A")
                mgr_details_block.append(f"""  - **Name**: {name}
    - **Education**: {edu}
    - **Experience**: {exp}
    - **Other Schemes Managed**: {other_funds}""")
            
            managers_str = ", ".join(managers) if managers else mf_data.get("fund_manager", "N/A")
            managers_detail_str = "\n".join(mgr_details_block) if mgr_details_block else "  - Details not available"
            
            # Format Holdings
            holdings = []
            for hold in mf_data.get("holdings", []):
                company = hold.get("company_name", "N/A")
                sector = hold.get("sector_name", "N/A")
                instrument = hold.get("instrument_name", "N/A")
                percentage = hold.get("corpus_per", 0.0)
                rating = hold.get("rating", "N/A")
                holdings.append(f"| {company} | {sector} | {instrument} | {percentage:.2f}% | {rating} |")
                
            holdings_table = "\n".join(holdings[:15]) if holdings else "| No holding details available |"
            
            markdown = f"""# {scheme_name}

## Scheme Overview
- **Scheme Name**: {scheme_name}
- **Fund House**: {mf_data.get('fund_house', 'HDFC Mutual Fund')}
- **Category**: {mf_data.get('category', 'N/A')} - {mf_data.get('sub_category', 'N/A')}
- **Riskometer / Risk**: {risk}
- **Launch Date**: {mf_data.get('launch_date', 'N/A')}
- **ISIN**: {mf_data.get('isin', 'N/A')}
- **Benchmark Index**: {mf_data.get('benchmark_name', mf_data.get('benchmark', 'N/A'))}

## Factual Scheme Metrics
- **Latest NAV**: ₹{mf_data.get('nav', 'N/A')} (As of {mf_data.get('nav_date', 'N/A')})
- **Expense Ratio**: {mf_data.get('expense_ratio', 'N/A')}%
- **Fund Size (AUM)**: ₹{mf_data.get('aum', 'N/A'):,} Cr
- **Minimum SIP Investment**: ₹{mf_data.get('min_sip_investment', 'N/A')}
- **Minimum Lumpsum Investment**: ₹{mf_data.get('min_investment_amount', 'N/A')}
- **Exit Load**: {mf_data.get('exit_load', 'N/A')}
- **Lock-in Period**: {lock_in_str}
- **Portfolio Turnover Ratio**: {mf_data.get('portfolio_turnover', 'N/A')}%

## Fund Management
- **Primary Fund Manager**: {managers_str}
- **Fund Manager Details**:
{managers_detail_str}

## Top Portfolio Holdings
| Company Name | Sector | Instrument | Assets (%) | Rating |
| :--- | :--- | :--- | :--- | :--- |
{holdings_table}

## Investment Objective
{mf_data.get('description', 'N/A')}

## Ingestion Metadata
- **Source URL**: {url}
- **Scraped At**: {scraped_at}
"""
            return {"type": "scheme", "markdown": markdown, "name": get_slug(url)}
            
        # Filter List Page Ingestion
        elif "initialSearchResults" in page_props:
            logging.info("Parsing Groww mutual fund filter list page")
            results = page_props["initialSearchResults"].get("content", [])
            
            table_rows = []
            for item in results:
                s_name = item.get("scheme_name", "N/A")
                cat = f"{item.get('category', 'N/A')} - {item.get('sub_category', 'N/A')}"
                risk = item.get("risk", "N/A")
                nav = item.get("nav", "N/A")
                aum = item.get("aum", "N/A")
                exp = item.get("expense_ratio", "N/A")
                exit_l = item.get("exit_load", "N/A")
                table_rows.append(f"| {s_name} | {cat} | {risk} | {nav} | {aum} | {exp}% | {exit_l} |")
                
            table_str = "\n".join(table_rows) if table_rows else "| No results available |"
            
            markdown = f"""# HDFC Mutual Funds Filter List

This document lists mutual fund schemes from HDFC Mutual Fund retrieved from the Groww filter page.

| Scheme Name | Category | Risk | NAV | AUM (Cr) | Expense Ratio | Exit Load |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{table_str}

## Ingestion Metadata
- **Source URL**: {url}
- **Scraped At**: {scraped_at}
"""
            return {"type": "filter", "markdown": markdown, "name": get_slug(url)}
            
        else:
            logging.warning(f"Next.js payload structure unrecognized for {url}. Falling back to text.")
            # Fallback
            main_content = soup.find(class_="layout-main") or soup.find(id="root") or soup.body
            body_text = main_content.get_text(separator="\n") if main_content else soup.get_text(separator="\n")
            markdown = f"""# Scraped Page: {url}

## Raw Content Fallback
{body_text}

## Ingestion Metadata
- **Source URL**: {url}
- **Scraped At**: {scraped_at}
"""
            return {"type": "fallback", "markdown": markdown, "name": get_slug(url)}
            
    except Exception as e:
        logging.error(f"Error parsing Next.js data for {url}: {e}")
        return None

def run_scraper():
    """Main function to trigger scraping of all 15 URLs."""
    logging.info("Starting Mutual Fund Groww Scraper Ingestion Process")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    session = requests.Session()
    success_count = 0
    
    for url in URLS:
        result = scrape_url(url, session)
        if result:
            file_name = f"{result['name']}.md"
            file_path = os.path.join(OUTPUT_DIR, file_name)
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(result["markdown"])
                logging.info(f"Saved scraped data to {file_path}")
                success_count += 1
            except Exception as e:
                logging.error(f"Failed to write data to {file_path}: {e}")
        else:
            logging.error(f"Failed to scrape URL: {url}")
            
    logging.info(f"Ingestion completed. Successfully processed {success_count}/{len(URLS)} URLs.")
    return success_count

if __name__ == "__main__":
    run_scraper()
