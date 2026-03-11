from pydantic import BaseModel, Field


class WCManualInput(BaseModel):

    # ---------------------------------------
    # CURRENT ASSETS / LIABILITIES
    # ---------------------------------------

    current_assets: float = Field(
        default=0,
        ge=0,
        description="Total Current Assets"
    )

    current_liabilities: float = Field(
        default=0,
        ge=0,
        description="Total Current Liabilities"
    )

    inventory: float = Field(
        default=0,
        ge=0,
        description="Stock / Inventory value"
    )

    receivables: float = Field(
        default=0,
        ge=0,
        description="Trade receivables / Sundry debtors"
    )

    payables: float = Field(
        default=0,
        ge=0,
        description="Trade creditors / Payables"
    )

    other_current_assets: float = Field(
        default=0,
        ge=0,
        description="Other current assets"
    )

    other_current_liabilities: float = Field(
        default=0,
        ge=0,
        description="Other current liabilities"
    )

    cash_bank: float = Field(
        default=0,
        ge=0,
        description="Cash and bank balance"
    )

    # ---------------------------------------
    # SALES / OPERATIONS
    # ---------------------------------------

    annual_sales: float = Field(
        default=0,
        ge=0,
        description="Annual turnover / sales"
    )

    cogs: float = Field(
        default=0,
        ge=0,
        description="Cost of goods sold"
    )

    bank_credit: float = Field(
        default=0,
        ge=0,
        description="Existing working capital borrowing"
    )

    # ---------------------------------------
    # NETWORTH COMPONENTS
    # ---------------------------------------

    equity_share_capital: float = Field(
        default=0,
        ge=0,
        description="Equity share capital"
    )

    reserves: float = Field(
        default=0,
        ge=0,
        description="Reserves and surplus"
    )

    # ---------------------------------------
    # DEBT STRUCTURE
    # ---------------------------------------

    short_term_debt: float = Field(
        default=0,
        ge=0,
        description="Short term borrowings"
    )

    long_term_debt: float = Field(
        default=0,
        ge=0,
        description="Long term borrowings"
    )

    unsecured_loans: float = Field(
        default=0,
        ge=0,
        description="Unsecured loans"
    )
