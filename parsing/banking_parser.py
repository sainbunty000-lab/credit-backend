def analyze_statement(df_data):
    """
    df_data: list of dicts from OCR
    Expected keys: 'date', 'debit', 'credit', 'balance'
    """
    required_keys = ['debit', 'credit']
    
    # Check if columns exist in the first row
    if not all(k in df_data[0] for k in required_keys):
        return {
            "status": "Not Readable",
            "reason": "Debit/Credit columns not detected"
        }

    total_credits = sum(float(row.get('credit', 0)) for row in df_data)
    total_debits = sum(float(row.get('debit', 0)) for row in df_data)
    
    # Logic for average balance and hygiene would go here...
    return {
        "total_credits": total_credits,
        "net_surplus": total_credits - total_debits,
        "status": "Success"
    }
