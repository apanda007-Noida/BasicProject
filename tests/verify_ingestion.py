import os
import re
import sys

OUTPUT_DIR = "data/ingested"
EXPECTED_FILES = [
    "hdfc-mid-cap-fund-direct-growth.md",
    "hdfc-small-cap-fund-direct-growth.md",
    "hdfc-gold-etf-fund-of-fund-direct-plan-growth.md",
    "hdfc-equity-fund-direct-growth.md",
    "hdfc-defence-fund-direct-growth.md",
    "hdfc-nifty-50-index-fund-direct-growth.md",
    "hdfc-large-and-mid-cap-fund-direct-growth.md",
    "hdfc-infrastructure-fund-direct-growth.md",
    "hdfc-mutual-funds-filter-list.md",
    "hdfc-banking-financial-services-fund-direct-growth.md",
    "hdfc-innovation-fund-direct-growth.md",
    "hdfc-premier-multi-cap-fund-direct-growth.md",
    "hdfc-diversified-equity-all-cap-active-fof-direct-growth.md",
    "hdfc-nifty-largemidcap-250-index-fund-direct-growth.md",
    "hdfc-bse-india-sector-leaders-index-fund-direct-growth.md"
]

REQUIRED_HEADINGS = [
    "## Scheme Overview",
    "## Factual Scheme Metrics",
    "## Fund Management",
    "## Top Portfolio Holdings",
    "## Investment Objective",
    "## Ingestion Metadata"
]

def verify_ingestion():
    print("=== Phase 1 Ingestion Verification ===")
    
    if not os.path.exists(OUTPUT_DIR):
        print(f"[FAIL] Output directory '{OUTPUT_DIR}' does not exist.")
        sys.exit(1)
        
    print(f"[PASS] Output directory '{OUTPUT_DIR}' exists.")
    
    all_passed = True
    missing_files = []
    
    for filename in EXPECTED_FILES:
        filepath = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(filepath):
            missing_files.append(filename)
            all_passed = False
            continue
            
        # Inspect contents
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        if not content.strip():
            print(f"[FAIL] File '{filename}' is empty.")
            all_passed = False
            continue
            
        # For filter list, check different headings
        if filename == "hdfc-mutual-funds-filter-list.md":
            if "| Scheme Name | Category | Risk | NAV |" not in content:
                print(f"[FAIL] Filter list file '{filename}' is missing the data table.")
                all_passed = False
            else:
                print(f"[PASS] '{filename}' successfully verified (contains data table).")
            continue
            
        # For scheme detail pages, check all required headings
        missing_headings = [h for h in REQUIRED_HEADINGS if h not in content]
        if missing_headings:
            print(f"[FAIL] Scheme file '{filename}' is missing required headings: {missing_headings}")
            all_passed = False
            continue
            
        # Check that key metrics are parsed (not N/A or empty where they should be present)
        # We can extract values using simple regex
        nav_match = re.search(r"-\s+\*\*Latest NAV\*\*:\s+([^\n]+)", content)
        exp_match = re.search(r"-\s+\*\*Expense Ratio\*\*:\s+([^\n]+)", content)
        aum_match = re.search(r"-\s+\*\*Fund Size \(AUM\)\*\*:\s+([^\n]+)", content)
        risk_match = re.search(r"-\s+\*\*Riskometer / Risk\*\*:\s+([^\n]+)", content)
        
        nav_val = nav_match.group(1) if nav_match else "Missing"
        exp_val = exp_match.group(1) if exp_match else "Missing"
        aum_val = aum_match.group(1) if aum_match else "Missing"
        risk_val = risk_match.group(1) if risk_match else "Missing"
        
        # Risk or NAV should not be N/A or Missing for these core funds
        if "N/A" in nav_val or "Missing" in nav_val:
            print(f"[WARN] '{filename}' has NAV value: {nav_val}")
        if "N/A" in risk_val or "Missing" in risk_val:
            print(f"[WARN] '{filename}' has Riskometer value: {risk_val}")
            
        # Clean up any unicode characters for console print
        nav_val_clean = nav_val.replace("\u20b9", "Rs.")
        aum_val_clean = aum_val.replace("\u20b9", "Rs.")
        print(f"[PASS] '{filename}' verified (NAV: {nav_val_clean}, Expense: {exp_val}, AUM: {aum_val_clean}, Risk: {risk_val})")
        
    if missing_files:
        print(f"[FAIL] Missing {len(missing_files)} expected files: {missing_files}")
        
    if all_passed:
        print("\n[SUCCESS] All 15 files successfully ingested, parsed, and verified!")
        sys.exit(0)
    else:
        print("\n[FAILURE] Verification encountered errors.")
        sys.exit(1)

if __name__ == "__main__":
    verify_ingestion()
