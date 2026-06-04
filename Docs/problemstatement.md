# Problem Statement: Mutual Fund FAQ Assistant (Facts-Only Q&A)

## Overview
The objective of this project is to build a facts-only FAQ assistant for mutual fund schemes, using **Groww** as the reference product context. The assistant will answer objective, verifiable queries related to mutual funds by retrieving information exclusively from official public sources, such as Asset Management Company (AMC) websites, AMFI, and SEBI.

The system must strictly avoid providing investment advice, opinions, or recommendations. Every response must include a single, clear source link and adhere to defined constraints around clarity, accuracy, and compliance.

## Objective
Design and implement a lightweight Retrieval-Augmented Generation (RAG)-based assistant that:
*   Answers factual queries about mutual fund schemes.
*   Uses a curated corpus of official documents.
*   Provides concise, source-backed responses.

## Target Users
*   **Retail investors** comparing mutual fund schemes.
*   **Customer support and content teams** handling repetitive mutual fund queries.

## Scope of Work

### 1. Corpus Definition
For this project, **HDFC Mutual Fund** has been selected as the target Asset Management Company (AMC). Below is the curated corpus of 15 official public URLs (using Groww as the reference platform context):

1.  HDFC Mid-Cap Opportunities Fund Direct Growth - https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth
2.  HDFC Small Cap Fund Direct Growth - https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth
3.  HDFC Gold ETF Fund of Fund Direct Plan Growth - https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth
4.  HDFC Flexi Cap Fund (formerly Equity Fund) Direct Growth - https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth
5.  HDFC Defence Fund Direct Growth - https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth
6.  HDFC Nifty 50 Index Fund Direct Growth - https://groww.in/mutual-funds/hdfc-nifty-50-index-fund-direct-growth
7.  HDFC Large and Mid Cap Fund Direct Growth - https://groww.in/mutual-funds/hdfc-large-and-mid-cap-fund-direct-growth
8.  HDFC Infrastructure Fund Direct Growth - https://groww.in/mutual-funds/hdfc-infrastructure-fund-direct-growth
9.  HDFC Mutual Funds Filter List - https://groww.in/mutual-funds/filter?fund_house=%5B%22HDFC+Mutual+Fund%22%5D
10. HDFC Banking & Financial Services Fund Direct Growth - https://groww.in/mutual-funds/hdfc-banking-financial-services-fund-direct-growth
11. HDFC Innovation Fund Direct Growth - https://groww.in/mutual-funds/hdfc-innovation-fund-direct-growth
12. HDFC Premier Multi Cap Fund Direct Growth - https://groww.in/mutual-funds/hdfc-premier-multi-cap-fund-direct-growth
13. HDFC Diversified Equity All Cap Active FoF Direct Growth - https://groww.in/mutual-funds/hdfc-diversified-equity-all-cap-active-fof-direct-growth
14. HDFC Nifty LargeMidcap 250 Index Fund Direct Growth - https://groww.in/mutual-funds/hdfc-nifty-largemidcap-250-index-fund-direct-growth
15. HDFC BSE India Sector Leaders Index Fund Direct Growth - https://groww.in/mutual-funds/hdfc-bse-india-sector-leaders-index-fund-direct-growth

These sources cover the required scheme documents, factsheets, download guidelines, and scheme parameters needed for the FAQ assistant.

### 2. FAQ Assistant Requirements
The assistant must answer facts-only queries, such as:
*   Expense ratio of a scheme
*   Exit load details
*   Minimum SIP amount
*   ELSS lock-in period
*   Riskometer classification
*   Benchmark index
*   Process to download statements or capital gains reports
*   Fund management data (e.g., fund manager name, tenure, and other managed schemes)

> [!IMPORTANT]
> **Response constraints:**
> *   Each response is limited to a maximum of **3 sentences**.
> *   Each response must include **exactly one citation link**.
> *   Each response must include a footer:
>     `Last updated from sources: <date>`

### 3. Refusal Handling
The assistant must refuse non-factual or advisory queries, such as:
*   *"Should I invest in this fund?"*
*   *"Which fund is better?"*

**Refusal responses must:**
*   Be polite and clearly worded.
*   Reinforce the facts-only limitation.
*   Provide a relevant educational link (e.g., AMFI or SEBI resource).

### 4. User Interface (Minimal)
The solution should include a simple interface with:
*   A welcome message
*   Three example questions
*   A visible disclaimer:
    > **Disclaimer:** Facts-only. No investment advice.

---

## Constraints

### Data and Sources
*   Use **only** official public sources (AMC, AMFI, SEBI).
*   Do **not** use third-party blogs or aggregator websites.

### Privacy and Security
Do **not** collect, store, or process:
*   PAN or Aadhaar numbers
*   Account numbers
*   OTPs
*   Email addresses or phone numbers

### Content Restrictions
*   No investment advice or recommendations.
*   No performance comparisons or return calculations.
*   For performance-related queries, provide a link to the official factsheet only.

### Transparency
*   Responses must be short, factual, and verifiable.
*   Every answer must include a source link and last updated date.

---

## Expected Deliverables

### README Document
*   Setup instructions
*   Selected AMC and schemes
*   Architecture overview (RAG approach)
*   Known limitations
*   Disclaimer Snippet:
    > **Disclaimer:** Facts-only. No investment advice.

---

## Success Criteria
*   Accurate retrieval of factual mutual fund information.
*   Strict adherence to facts-only responses.
*   Consistent inclusion of valid source citations.
*   Proper refusal of advisory queries.
*   Clean, minimal, and user-friendly interface.

---

## Summary
The goal is to build a trustworthy, transparent, and compliant mutual fund FAQ assistant that prioritizes accuracy over intelligence. The system should ensure that users receive only verified, source-backed financial information, without any advisory bias or speculative content.
