from typing import List
from abc import ABC, abstractmethod

class TreeNode(ABC):
    """Base class for the Portfolio hierarchy tree."""
    def __init__(self, name: str):
        self.name = name
        self.children: List['TreeNode'] = []

    def add_child(self, child: 'TreeNode'):
        self.children.append(child)

    @abstractmethod
    def get_value(self) -> float:
        """Recursively calculate value."""
        pass

    def display(self, level: int = 0):
        """Helper to print the tree structure."""
        indent = "  " * level
        value = self.get_value()
        print(f"{indent}- {self.name}: ${value:.2f}")
        for child in self.children:
            child.display(level + 1)


class CompanyNode(TreeNode):
    """Leaf node representing an actual company holding."""
    def __init__(self, ticker: str, shares: float, current_price: float):
        super().__init__(name=ticker)
        self.ticker = ticker
        self.shares = shares
        self.current_price = current_price

    def get_value(self) -> float:
        return self.shares * self.current_price


class SectorNode(TreeNode):
    """Intermediate node grouping companies by sector."""
    def get_value(self) -> float:
        return sum(child.get_value() for child in self.children)


class PortfolioRootNode(TreeNode):
    """Root node for the entire portfolio tree."""
    def __init__(self, name: str, cash_balance: float = 0.0):
        super().__init__(name)
        self.cash_balance = cash_balance

    def get_value(self) -> float:
        # Portfolio value is cash + value of all sectors
        return self.cash_balance + sum(child.get_value() for child in self.children)
