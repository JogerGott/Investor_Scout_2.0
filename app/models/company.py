from dataclasses import dataclass
from typing import Optional

@dataclass
class Company:
    """
    Static/Infrequent qualitative data about a specific company.
    """
    ticker: str
    name: str
    sector: str
    industry: str
    moat: Optional[str] = None
    business_model: Optional[str] = None
    company_stage: Optional[str] = None  # e.g., Growth, Value, Cyclical

    def __post_init__(self):
        self.ticker = self.ticker.upper()
