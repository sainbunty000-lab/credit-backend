from utils.safe_math import default_zero

def calculate_agriculture(data: dict):

    total_income = default_zero(data.get("total_income"))
    tax = default_zero(data.get("tax"))
    monthly_undoc = default_zero(data.get("monthly_undocumented_income"))
    monthly_emi = default_zero(data.get("monthly_emi"))

    documented = total_income - tax
    annual_undoc = monthly_undoc * 12
    annual_emi = monthly_emi * 12

    total_net = documented + annual_undoc - annual_emi
    total_net = max(total_net, 0)

    eligibility = total_net / 0.14 if total_net > 0 else 0
    lakhs = eligibility / 100000

    return {
        "tenure_years": 5,
        "eligibility_rupees": round(eligibility, 2),
        "eligibility_lakhs_display": f"Eligibility (Lakhs) = {round(lakhs,2)} Lakhs",
        "status": "Eligible" if eligibility > 0 else "Not Eligible"
    }
