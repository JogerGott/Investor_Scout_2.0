from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime
from app.data_structures.transaction_ll import TransactionLinkedList
from app.data_structures.transaction_node import TransactionNode
from app.models.holding import Holding

@dataclass
class Portfolio:
    portfolio_id: int
    user_id: int
    name: str
    cash_balance: float
    transaction_log: TransactionLinkedList = field(default_factory=TransactionLinkedList)
    holdings: Dict[str, Holding] = field(default_factory=dict) 
    
    def add_transaction(self, ticker: str, trans_type: str, shares: float, price: float, date: datetime):
        """
        Appends the transaction to the Immutable List and then immediately recalcs the holdings.
        """
        node = TransactionNode(ticker, trans_type, shares, price, date)
        self.transaction_log.append(node)
        
        # When buying, deduct from cash. When selling, add to cash.
        if node.transaction_type == 'BUY':
            if self.cash_balance < (shares * price):
                raise ValueError("Insufficient cash to perform BUY.")
            self.cash_balance -= (shares * price)
        elif node.transaction_type == 'SELL':
            self.cash_balance += (shares * price)

        # Refresh holding dictionary by iterating the log (or simply updating it implicitly based on type)
        # To maintain perfect stateless-ish structure, we completely rebuild the holdings dict from the log:
        self._recalculate_holdings()

    def _recalculate_holdings(self):
        """
        The core of the architecture. The true state of the Portfolio Holdings 
        is ONLY derived from playing back the transaction log from node 1 to N.
        """
        temp_holdings: Dict[str, Holding] = {}
        
        for tx in self.transaction_log:
            ticker = tx.ticker
            
            if ticker not in temp_holdings:
                if tx.transaction_type == 'SELL':
                    raise ValueError(f"Transaction log error: SELL before BUY for {ticker}")
                temp_holdings[ticker] = Holding(ticker=ticker, shares=tx.shares, avg_cost=tx.price)
            else:
                holding = temp_holdings[ticker]
                if tx.transaction_type == 'BUY':
                    # Calculate new average cost
                    total_value_before = holding.shares * holding.avg_cost
                    new_value = tx.shares * tx.price
                    holding.shares += tx.shares
                    holding.avg_cost = (total_value_before + new_value) / holding.shares
                elif tx.transaction_type == 'SELL':
                    holding.shares -= tx.shares
                    if holding.shares < 0:
                        raise ValueError(f"Log Error: Short selling isn't supported. {ticker} shares dropped below 0")
                    elif holding.shares == 0:
                        holding.avg_cost = 0.0

        # Remove 0-share holdings to keep dict clean
        self.holdings = {k: v for k, v in temp_holdings.items() if v.shares > 0}

    def get_total_value(self) -> float:
        """
        Calculates value = cash + (sum of all current_value of holdings).
        Assumes holding.current_value is updated externally by a pricing service.
        """
        holdings_value = sum(h.current_value for h in self.holdings.values())
        return self.cash_balance + holdings_value
