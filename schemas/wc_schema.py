from pydantic import BaseModel


class WCManualInput(BaseModel):

    current_assets: float = 0
    current_liabilities: float = 0

    inventory: float = 0
    receivables: float = 0
    payables: float = 0

    annual_sales: float = 0
    cogs: float = 0

    bank_credit: float = 0

    other_current_assets: float = 0
    other_current_liabilities: float = 0

    cash_bank: float = 0

    equity_share_capital: float = 0
    reserves: float = 0

    short_term_debt: float = 0
    long_term_debt: float = 0
    unsecured_loans: float = 0
