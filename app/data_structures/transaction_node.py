from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class TransactionNode:
    """
    An immutable node in the transaction history LinkedList.
    Transactions map either to 'BUY' or 'SELL'.
    """
    ticker: str
    transaction_type: str  # 'BUY' or 'SELL'
    shares: float
    price: float
    date: datetime
    next: Optional['TransactionNode'] = None

    def __post_init__(self):
        self.ticker = self.ticker.upper()
        self.transaction_type = self.transaction_type.upper()
