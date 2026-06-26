from dataclasses import dataclass, field
from typing import List, Any, Optional

@dataclass
class User:
    user_id: int
    first_name: str
    last_name: str
    email: str
    password_hash: str
    telephone: Optional[str] = None
    portfolios: List[Any] = field(default_factory=list) # List of Portfolio objects

    def get_total_net_worth(self) -> float:
        """
        Iterates over all portfolios and sums up their total calculated value.
        """
        worth = 0.0
        for p in self.portfolios:
            worth += p.get_total_value()
        return worth
