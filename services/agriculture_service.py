from utils.safe_math import safe_divide, safe_subtract, default_zero
import math


def calculate_agri_logic(doc_inc, tax, undoc_m, emi_m,
                         tenure_years=5,
                         interest_rate=12):

    # =============================
    # INPUT NORMALIZATION
    # =============================

    D = default_zero(doc_inc)
    T = default_zero(tax)
    U = default_zero(undoc_m)
    EMI_existing_m = default_zero(emi_m)

    tenure_years = default_zero(tenure_years)
    interest_rate = default_zero(interest_rate)

    # =============================
    # POLICY ADJUSTMENTS
    # =============================

    net_doc = safe_subtract(D, T)
    adj_doc = 0.70 * net_doc

    annual_undoc = U * 12
    adj_undoc = 0.42 * annual_undoc

    total_income = adj_doc + adj_undoc
    annual_existing_emi = EMI_existing_m * 12
    disposable_income = safe_subtract(total_income, annual_existing_emi)

    # =============================
    # FOIR CALCULATION
    # =============================

    monthly_income = total_income / 12 if total_income > 0 else 0

    foir_percent = (
        safe_divide(EMI_existing_m, monthly_income) * 100
        if monthly_income > 0 else 0
    )

    max_foir_allowed = 60

    max_new_emi = (
        (monthly_income * max_foir_allowed / 100) - EMI_existing_m
        if monthly_income > 0 else 0
    )

    if max_new_emi < 0:
        max_new_emi = 0

    # =============================
    # LOAN ELIGIBILITY - DUAL MODEL
    # =============================

    # ----- MODEL 1: EMI FORMULA -----
    r = interest_rate / 100 / 12
    n = tenure_years * 12

    if r > 0:
        eligible_loan_emi_model = max_new_emi * ((1 + r) ** n - 1) / (r * (1 + r) ** n)
    else:
        eligible_loan_emi_model = max_new_emi * n

    # ----- MODEL 2: POLICY MULTIPLIER -----
    if disposable_income > 0:
        eligible_loan_policy_model = disposable_income / 0.14
    else:
        eligible_loan_policy_model = 0

    # ----- FINAL CONSERVATIVE -----
    eligible_loan = min(eligible_loan_emi_model, eligible_loan_policy_model)

    # =============================
    # REJECTION CONDITIONS
    # =============================

    status = "Eligible"
    rejection_reason = None

    if disposable_income <= 0:
        status = "Rejected"
        rejection_reason = "Negative disposable income"

    elif foir_percent > max_foir_allowed:
        status = "Rejected"
        rejection_reason = "FOIR exceeds policy limit"

    # =============================
    # RISK SCORING
    # =============================

    score = 100

    if foir_percent > 50:
        score -= 30
    elif 35 <= foir_percent <= 50:
        score -= 15

    if disposable_income < (1.5 * annual_existing_emi):
        score -= 20

    if adj_undoc > adj_doc:
        score -= 10

    agri_score = max(0, min(score, 100))

    # =============================
    # RISK GRADE
    # =============================

    if agri_score >= 80:
        risk_grade = "A"
    elif agri_score >= 65:
        risk_grade = "B"
    elif agri_score >= 50:
        risk_grade = "C"
    else:
        risk_grade = "D"

    # =============================
    # CHART DATA
    # =============================

    chart_data = {
        "income_split": {
            "documented": round(adj_doc, 2),
            "undocumented": round(adj_undoc, 2)
        },
        "foir_analysis": {
            "foir_percent": round(foir_percent, 2),
            "max_allowed": max_foir_allowed
        }
    }

    # =============================
    # FINAL RESPONSE
    # =============================

    return {
        "adjusted_documented_income": round(adj_doc, 2),
        "adjusted_undocumented_income": round(adj_undoc, 2),
        "total_adjusted_income": round(total_income, 2),
        "monthly_income": round(monthly_income, 2),
        "annual_existing_emi": round(annual_existing_emi, 2),
        "disposable_income": round(disposable_income, 2),
        "foir_percent": round(foir_percent, 2),
        "max_new_emi_allowed": round(max_new_emi, 2),

        # Dual model outputs
        "eligible_loan_emi_model": round(eligible_loan_emi_model, 2),
        "eligible_loan_policy_model": round(eligible_loan_policy_model, 2),
        "eligible_loan_amount": round(eligible_loan, 2),

        "agri_score": agri_score,
        "risk_grade": risk_grade,
        "status": status,
        "rejection_reason": rejection_reason,
        "chart_data": chart_data
    }
