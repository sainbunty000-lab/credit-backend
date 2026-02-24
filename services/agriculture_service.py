from utils.safe_math import safe_divide, safe_subtract, default_zero


def calculate_agri_logic(doc_inc, tax, undoc_m, emi_m):

    # Convert inputs
    D = default_zero(doc_inc)
    T = default_zero(tax)
    U = default_zero(undoc_m)
    EMI_m = default_zero(emi_m)

    # =============================
    # POLICY OPTION A
    # =============================
    net_doc = safe_subtract(D, T)
    adj_doc = 0.70 * net_doc

    annual_undoc = U * 12
    adj_undoc = 0.42 * annual_undoc

    total_income = adj_doc + adj_undoc
    annual_emi = EMI_m * 12

    disposable = safe_subtract(total_income, annual_emi)

    emi_ratio = safe_divide(annual_emi, total_income) * 100
    eligibility = safe_divide(disposable, 0.14)

    # =============================
    # REJECTION CONDITIONS
    # =============================
    status = "Eligible"
    rejection_reason = None

    if disposable <= 0:
        status = "Rejected"
        rejection_reason = "Negative disposable income"

    elif emi_ratio > 60:
        status = "Rejected"
        rejection_reason = "EMI ratio exceeds 60%"

    # =============================
    # CONDITIONAL REDUCTION
    # =============================
    if 40 < emi_ratio <= 60:
        eligibility *= 0.80

    # =============================
    # AGRI RISK SCORE
    # =============================
    score = 100

    if emi_ratio > 50:
        score -= 30
    elif 30 <= emi_ratio <= 50:
        score -= 15

    if disposable < (1.5 * annual_emi):
        score -= 20

    agri_score = max(0, min(100, score))

    return {
        "adjusted_documented_income": round(adj_doc, 2),
        "adjusted_undocumented_income": round(adj_undoc, 2),
        "total_adjusted_income": round(total_income, 2),
        "annual_emi": round(annual_emi, 2),
        "disposable_income": round(disposable, 2),
        "emi_ratio": round(emi_ratio, 2),
        "loan_eligibility": round(eligibility, 2),
        "agri_score": agri_score,
        "status": status,
        "rejection_reason": rejection_reason,
    }
