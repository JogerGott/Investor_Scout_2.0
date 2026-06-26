from app.models.portfolio import Portfolio
from app.data_structures.stock_cache import StockCache
from typing import Dict, Any

class PortfolioService:
    """
    Business Logic Layer for Portfolios.
    Handles calculations that require joining the Portfolio state with external data (like StockCache)
    or running complex historical algorithms (Realized P&L).
    """
    def __init__(self, stock_cache: StockCache):
        self.stock_cache = stock_cache

    def get_portfolio_metrics(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Calculates Realized P&L, Unrealized P&L, Total Value, and current allocation.
        """
        total_value = portfolio.cash_balance
        unrealized_pnl = 0.0
        
        # Calculate Realized P&L from the transaction log
        realized_pnl = self._calculate_realized_pnl(portfolio)
        
        allocations = {"Cash": portfolio.cash_balance}
        
        # Calculate Unrealized P&L using real-time prices
        for ticker, holding in portfolio.holdings.items():
            current_price = self.stock_cache.get_price(ticker)
            if not current_price:
                # Fallback to cost if API fails and cache is empty
                current_price = holding.avg_cost 
                
            holding.update_value(current_price)
            
            value = holding.current_value
            total_value += value
            
            # Unrealized = (current_price - avg_cost) * shares
            unrealized_pnl += (current_price - holding.avg_cost) * holding.shares
            
            allocations[ticker] = value
            
        # Convert absolute value allocations to percentages
        allocation_percentages = {}
        if total_value > 0:
            for k, v in allocations.items():
                allocation_percentages[k] = round((v / total_value) * 100, 2)
                
        return {
            "Total Value": total_value,
            "Cash Balance": portfolio.cash_balance,
            "Realized P&L": realized_pnl,
            "Unrealized P&L": unrealized_pnl,
            "Allocations (%)": allocation_percentages
        }

    def _calculate_realized_pnl(self, portfolio: Portfolio) -> float:
        """
        Replays the immutable transaction log to precisely calculate realized gains/losses 
        from all SELL events using the moving average cost basis.
        """
        realized_pnl = 0.0
        # Temporary tracker to reconstruct the avg_cost historically step-by-step
        cost_basis_tracker = {}
        
        for tx in portfolio.transaction_log:
            ticker = tx.ticker
            if ticker not in cost_basis_tracker:
                cost_basis_tracker[ticker] = {"shares": 0.0, "avg_cost": 0.0}
                
            tracker = cost_basis_tracker[ticker]
            
            if tx.transaction_type == 'BUY':
                total_val_before = tracker["shares"] * tracker["avg_cost"]
                new_val = tx.shares * tx.price
                tracker["shares"] += tx.shares
                tracker["avg_cost"] = (total_val_before + new_val) / tracker["shares"]
            elif tx.transaction_type == 'SELL':
                # Realized Profit/Loss = shares_sold * (sell_price - avg_cost_at_time_of_sale)
                profit = tx.shares * (tx.price - tracker["avg_cost"])
                realized_pnl += profit
                
                tracker["shares"] -= tx.shares
                if tracker["shares"] == 0:
                    tracker["avg_cost"] = 0.0
                    
        return realized_pnl
