from parsing.accounting_dictionary import ACCOUNTING_MAP

def normalize_text(text):
    """Clean text for better matching."""
    return text.lower().strip().replace("_", " ").replace("-", " ")

def extract_financial_values(extracted_data: dict):
    """
    Input: {'Sales': 500000, 'Current Assets': 200000, 'Misc': 100}
    Output: {'annual_sales': 500000, 'current_assets': 200000, ...}
    """
    result = {
        "current_assets": 0,
        "current_liabilities": 0,
        "annual_sales": 0,
        "documented_income": 0,
        "tax_paid": 0
    }

    for raw_key, value in extracted_data.items():
        clean_key = normalize_text(raw_key)
        
        # Match against our hardcoded dictionary
        for standard_field, synonyms in ACCOUNTING_MAP.items():
            if any(synonym in clean_key for synonym in synonyms):
                # Only update if we haven't found a better match yet (or add them)
                result[standard_field] = float(value or 0)
                
    return result
