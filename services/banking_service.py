from utils.safe_math import safe_divide, default_zero

def analyze_banking(transactions, months_count=1):
    m = max(1, months_count)
    credits = sum(default_zero(t.get('credit')) for t in transactions)
    debits = sum(default_zero(t.get('debit')) for t in transactions)
    
    # Perfios Logic
    avg_credit = credits / m
    avg_debit = debits / m
    surplus = avg_credit - avg_debit
    
    # EMI & Bounce detection logic (Simplified for summary)
    bounces = [t for t in transactions if "return" in str(t.get('desc','')).lower()]
    
    return {
        "avg_monthly_credit": round(avg_credit, 2),
        "avg_monthly_debit": round(avg_debit, 2),
        "net_monthly_surplus": round(surplus, 2),
        "bounce_count": len(bounces),
        "hygiene": "Healthy" if len(bounces) == 0 and surplus > 0 else "Risky"
    }
