from dataclasses import dataclass
from typing import Optional

@dataclass
class FinancialSnapshot:
    """
    Historical quantitative facts generated each quarter to track a company's financial evolution.
    """
    ticker: str
    period_date: str  # e.g., 'Q1 2024'
    current_price: float
    roe: Optional[float] = None
    roa: Optional[float] = None
    debt_levels: Optional[float] = None
    margins: Optional[float] = None

    def __post_init__(self):
        self.ticker = self.ticker.upper()
