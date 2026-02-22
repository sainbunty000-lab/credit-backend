from utils.safe_math import safe_subtract, safe_divide, default_zero

def calculate_agri_logic(doc_inc, tax, undoc_m, emi_m):
    # Step 1 & 2
    net_doc = safe_subtract(default_zero(doc_inc), default_zero(tax))
    ann_undoc = default_zero(undoc_m) * 12
    ann_emi = default_zero(emi_m) * 12
    
    # Step 3
    total_net = safe_subtract((net_doc + ann_undoc), ann_emi)
    
    # Step 4 (5-Year Rule)
    eligibility = safe_divide(total_net, 0.14)
    
    return {
        "net_documented_income": round(net_doc, 2),
        "annual_undocumented_income": round(ann_undoc, 2),
        "annual_emi": round(ann_emi, 2),
        "total_net_income": round(total_net, 2),
        "loan_eligibility": round(eligibility, 2),
        "status": "Eligible" if eligibility > 0 else "Not Eligible"
    }
