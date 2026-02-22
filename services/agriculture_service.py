from utils.safe_math import safe_subtract, safe_divide

def calculate_agri_eligibility(doc_income, tax, monthly_undoc, monthly_emi):
    # Annual Conversions
    net_doc_income = safe_subtract(doc_income, tax)
    annual_undoc = float(monthly_undoc or 0) * 12
    annual_emi = float(monthly_emi or 0) * 12
    
    # Total Net Income
    total_net_income = safe_subtract((net_doc_income + annual_undoc), annual_emi)
    
    # Final Eligibility (5-year rule approx via 0.14 factor)
    loan_eligibility = safe_divide(total_net_income, 0.14)
    
    return {
        "total_net_income": round(total_net_income, 2),
        "loan_eligibility": round(loan_eligibility, 2),
        "status": "Eligible" if loan_eligibility > 0 else "Not Eligible"
    }
