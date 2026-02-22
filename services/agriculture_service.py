from utils.safe_math import default_zero

def calculate_agriculture(data: dict):

    total_income = default_zero(data.get("total_income"))
    tax = default_zero(data.get("tax"))
    monthly_undocumented = default_zero(data.get("monthly_undocumented_income"))
    monthly_emi = default_zero(data.get("monthly_emi"))

    documented_income = total_income - tax
    annual_undocumented = monthly_undocumented * 12
    annual_emi = monthly_emi * 12

    total_net_income = documented_income + annual_undocumented - annual_emi

    if total_net_income < 0:
        total_net_income = 0

    eligibility = total_net_income / 0.14 if total_net_income > 0 else 0
    eligibility_lakhs = eligibility / 100000

    status = "Eligible" if eligibility > 0 else "Not Eligible"

    return {
        "tenure_years": 5,
        "eligibility_rupees": round(eligibility, 2),
        "eligibility_lakhs_display": f"Eligibility (Lakhs) = {round(eligibility_lakhs, 2)} Lakhs",
        "status": status
    }
