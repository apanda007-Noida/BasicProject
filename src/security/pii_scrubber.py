import re

# Regex patterns for core PII entities
PAN_PATTERN = re.compile(r"\b[a-zA-Z]{5}[0-9]{4}[a-zA-Z]{1}\b")
AADHAAR_PATTERN = re.compile(r"\b[0-9]{4}\s*[0-9]{4}\s*[0-9]{4}\b|\b[0-9]{12}\b")
EMAIL_PATTERN = re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b")
PHONE_PATTERN = re.compile(r"\+?\b(?:\d{1,3}[- ]?)?\d{10}\b")
ACCOUNT_PATTERN = re.compile(r"\b\d{9,18}\b") # matches typical Indian bank account numbers

def scrub_pii(text: str) -> str:
    """
    Scrub sensitive PII from the text and replace with standard tokens.
    Converts numbers in contexts suggesting OTPs to [REDACTED_OTP].
    """
    if not text:
        return text

    # 1. Scrub PAN Card Numbers
    text = PAN_PATTERN.sub("[REDACTED_PAN]", text)
    
    # 2. Scrub Aadhaar Card Numbers
    text = AADHAAR_PATTERN.sub("[REDACTED_AADHAAR]", text)
    
    # 3. Scrub Email Addresses
    text = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    
    # 4. Scrub Phone Numbers
    text = PHONE_PATTERN.sub("[REDACTED_PHONE]", text)
    
    # 5. Scrub OTPs (Context-Aware)
    # We only scrub 4-6 digit numbers as OTP if the query contains words like "otp", "code", "pin", "verification"
    otp_context = any(w in text.lower() for w in ["otp", "code", "pin", "verification", "password"])
    if otp_context:
        # Match 4 to 6 digit numbers
        text = re.sub(r"\b\d{4,6}\b", "[REDACTED_OTP]", text)
        
    # 6. Scrub Bank Account / Credit Card Numbers
    # Make sure we don't accidentally match redacted OTPs or other tokens
    # We run this after others, matching 9-18 digit numbers that aren't inside brackets
    text = re.sub(r"\b(?<!\[)\d{9,18}(?!\])\b", "[REDACTED_ACCOUNT]", text)
    
    return text

if __name__ == "__main__":
    # Test cases
    test_cases = [
        "My email is test.user@gmail.com and phone is 9876543210.",
        "My PAN is ABCDE1234F and Aadhaar is 1234 5678 9012.",
        "The bank account number is 12345678901234.",
        "Here is the OTP code: 4821.",
        "Minimum SIP is 1000 and launch date is 2013." # Should NOT redact 1000 or 2013 as OTP
    ]
    
    print("=== Testing PII Scrubber ===")
    for tc in test_cases:
        print(f"Original: {tc}")
        print(f"Scrubbed: {scrub_pii(tc)}")
        print("-" * 30)
