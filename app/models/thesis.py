from dataclasses import dataclass

@dataclass
class Thesis:
    """
    AI-generated qualitative thesis representing the logic mapping behind an investment.
    """
    ticker: str
    key_aspects: str
    watch_conditions: str
    pain_points: str
    exit_strategy: str

    def __post_init__(self):
        self.ticker = self.ticker.upper()
