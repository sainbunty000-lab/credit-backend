from utils.safe_math import safe_divide, safe_subtract


def calculate_wc_logic(data):

    # ===============================
    # INPUT VALUES
    # ===============================

    ca = float(data.get("current_assets", 0))
    cl = float(data.get("current_liabilities", 0))
    inventory = float(data.get("inventory", 0))
    receivables = float(data.get("receivables", 0))
    payables = float(data.get("payables", 0))
    sales = float(data.get("annual_sales", 0))
    cogs = float(data.get("cogs", 0))
    bank_credit = float(data.get("bank_credit", 0))

    # ===============================
    # 1️⃣ NWC METHOD
    # ===============================

    nwc = safe_subtract(ca, cl)
    current_ratio = safe_divide(ca, cl)
    quick_ratio = safe_divide(ca - inventory, cl)

    # ===============================
    # 2️⃣ TURNOVER METHOD (NAYAK)
    # ===============================

    wc_requirement_turnover = sales * 0.25
    borrower_contribution_turnover = sales * 0.05
    bank_finance_turnover = sales * 0.20   # ✅ 20% Bank Finance

    # ===============================
    # 3️⃣ MPBF METHOD (TANDON - METHOD 2)
    # ===============================

    wc_gap = safe_subtract(ca, cl - bank_credit)

    borrower_contribution_mpbf = ca * 0.25

    mpbf = safe_subtract(wc_gap, borrower_contribution_mpbf)

    # ===============================
    # WORKING CAPITAL CYCLE
    # ===============================

    inventory_days = safe_divide(inventory, cogs) * 365
    receivable_days = safe_divide(receivables, sales) * 365
    payable_days = safe_divide(payables, cogs) * 365

    operating_cycle = inventory_days + receivable_days
    gap_days = operating_cycle - payable_days

    # ===============================
    # FINAL RECOMMENDED LIMIT
    # ===============================

    recommended_limit = max(bank_finance_turnover, mpbf)

    if recommended_limit <= 0:
        sanction_status = "Not Eligible"
    elif current_ratio >= 1.5:
        sanction_status = "Eligible - Recommend Sanction"
    else:
        sanction_status = "Conditional Approval"

    # ===============================
    # CHART READY STRUCTURE
    # ===============================

    chart_data = {
        "methods": {
            "turnover_method": round(bank_finance_turnover, 2),
            "mpbf_method": round(mpbf, 2)
        },
        "ratios": {
            "current_ratio": round(current_ratio, 2),
            "quick_ratio": round(quick_ratio, 2)
        },
        "cycle_days": {
            "inventory_days": round(inventory_days, 2),
            "receivable_days": round(receivable_days, 2),
            "payable_days": round(payable_days, 2),
            "gap_days": round(gap_days, 2)
        }
    }

    # ===============================
    # FINAL RESPONSE
    # ===============================

    return {
        "nwc": round(nwc, 2),
        "current_ratio": round(current_ratio, 2),
        "quick_ratio": round(quick_ratio, 2),

        # Turnover Method
        "wc_requirement_turnover": round(wc_requirement_turnover, 2),
        "borrower_contribution_turnover": round(borrower_contribution_turnover, 2),
        "bank_finance_turnover": round(bank_finance_turnover, 2),

        # MPBF Method
        "wc_gap": round(wc_gap, 2),
        "borrower_contribution_mpbf": round(borrower_contribution_mpbf, 2),
        "mpbf": round(mpbf, 2),

        # Final Decision
        "recommended_limit": round(recommended_limit, 2),
        "sanction_status": sanction_status,

        # Charts
        "chart_data": chart_data
    }
