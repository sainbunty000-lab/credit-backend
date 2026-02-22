def validate_document_readability(extracted_text):
    critical_keywords = ["date", "balance", "credit", "debit"]
    found = [word for word in critical_keywords if word in extracted_text.lower()]
    
    if len(found) < 3: # If we don't find most columns
        return {
            "readable": False,
            "status": "Not Readable",
            "reason": "Missing critical columns: Date, Credit, or Balance"
        }
    return {"readable": True}
