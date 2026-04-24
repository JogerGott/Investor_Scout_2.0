from dataclasses import dataclass

@dataclass
class Holding:
    """
    Active Portfolio Asset. This is a dynamically generated record.
    It's computed based on the transaction log LinkedList dynamically.
    """
    ticker: str
    shares: float
    avg_cost: float
    current_value: float = 0.0

    def update_value(self, current_price: float):
        self.current_value = self.shares * current_price
