from utils.safe_math import safe_divide, safe_subtract, default_zero
import math


def calculate_agri_logic(
    doc_inc,
    tax,
    undoc_m,
    emi_m,
    tenure_years=5,
    interest_rate=12
):

    # =====================================
    # INPUT NORMALIZATION
    # =====================================

    documented_income = default_zero(doc_inc)
    tax_paid = default_zero(tax)
    undocumented_monthly = default_zero(undoc_m)
    existing_emi_monthly = default_zero(emi_m)

    tenure_years = default_zero(tenure_years)
    interest_rate = default_zero(interest_rate)

    # =====================================
    # POLICY ADJUSTMENTS
    # =====================================

    net_documented_income = safe_subtract(documented_income, tax_paid)

    adjusted_documented_income = 0.70 * net_documented_income

    annual_undocumented_income = undocumented_monthly * 12

    adjusted_undocumented_income = 0.42 * annual_undocumented_income

    total_adjusted_income = (
        adjusted_documented_income + adjusted_undocumented_income
    )

    annual_existing_emi = existing_emi_monthly * 12

    disposable_income = safe_subtract(
        total_adjusted_income,
        annual_existing_emi
    )

    # =====================================
    # FOIR CALCULATION
    # =====================================

    monthly_income = safe_divide(total_adjusted_income, 12)

    foir_percent = safe_divide(
        existing_emi_monthly,
        monthly_income
    ) * 100

    max_foir_allowed = 60

    max_new_emi_allowed = (
        (monthly_income * max_foir_allowed / 100)
        - existing_emi_monthly
    )

    if max_new_emi_allowed < 0:
        max_new_emi_allowed = 0

    # =====================================
    # LOAN ELIGIBILITY MODEL 1 (EMI MODEL)
    # =====================================

    r = interest_rate / 100 / 12
    n = tenure_years * 12

    if r > 0:

        eligible_loan_emi_model = (
            max_new_emi_allowed
            * ((1 + r) ** n - 1)
            / (r * (1 + r) ** n)
        )

    else:

        eligible_loan_emi_model = max_new_emi_allowed * n

    # =====================================
    # LOAN ELIGIBILITY MODEL 2 (POLICY MODEL)
    # =====================================

    if disposable_income > 0:

        eligible_loan_policy_model = disposable_income / 0.14

    else:

        eligible_loan_policy_model = 0

    # =====================================
    # FINAL CONSERVATIVE ELIGIBILITY
    # =====================================

    final_eligible_loan = min(
        eligible_loan_emi_model,
        eligible_loan_policy_model
    )

    # =====================================
    # REJECTION CONDITIONS
    # =====================================

    status = "Eligible"
    rejection_reason = None

    if disposable_income <= 0:

        status = "Rejected"
        rejection_reason = "Negative disposable income"

    elif foir_percent > max_foir_allowed:

        status = "Rejected"
        rejection_reason = "FOIR exceeds policy limit"

    # =====================================
    # RISK SCORING
    # =====================================

    score = 100

    if foir_percent > 50:
        score -= 30

    elif 35 <= foir_percent <= 50:
        score -= 15

    if disposable_income < (1.5 * annual_existing_emi):
        score -= 20

    if adjusted_undocumented_income > adjusted_documented_income:
        score -= 10

    agri_score = max(0, min(score, 100))

    # =====================================
    # RISK GRADE
    # =====================================

    if agri_score >= 80:
        risk_grade = "A"

    elif agri_score >= 65:
        risk_grade = "B"

    elif agri_score >= 50:
        risk_grade = "C"

    else:
        risk_grade = "D"

    # =====================================
    # CHART DATA (FOR FRONTEND)
    # =====================================

    chart_data = {

        "income_split": [
            {
                "name": "Documented",
                "value": round(adjusted_documented_income, 2)
            },
            {
                "name": "Undocumented",
                "value": round(adjusted_undocumented_income, 2)
            }
        ],

        "foir_analysis": [
            {
                "name": "Current FOIR",
                "value": round(foir_percent, 2)
            },
            {
                "name": "Policy Limit",
                "value": max_foir_allowed
            }
        ]
    }

    # =====================================
    # CLEAN FUNCTION
    # =====================================

    def clean(value):

        if isinstance(value, float) and (
            math.isnan(value) or math.isinf(value)
        ):
            return 0

        return round(value, 2)

    # =====================================
    # FINAL RESPONSE
    # =====================================

    return {

        "income_analysis": {
            "adjusted_documented_income": clean(adjusted_documented_income),
            "adjusted_undocumented_income": clean(adjusted_undocumented_income),
            "total_adjusted_income": clean(total_adjusted_income),
            "monthly_income": clean(monthly_income)
        },

        "emi_analysis": {
            "annual_existing_emi": clean(annual_existing_emi),
            "disposable_income": clean(disposable_income),
            "foir_percent": clean(foir_percent),
            "max_new_emi_allowed": clean(max_new_emi_allowed)
        },

        "loan_eligibility": {
            "eligible_loan_emi_model": clean(eligible_loan_emi_model),
            "eligible_loan_policy_model": clean(eligible_loan_policy_model),
            "final_eligible_loan": clean(final_eligible_loan)
        },

        "risk": {
            "agri_score": agri_score,
            "risk_grade": risk_grade
        },

        "status": status,
        "rejection_reason": rejection_reason,

        "charts": chart_data
    }
