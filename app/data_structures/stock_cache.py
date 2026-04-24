import yfinance as yf
from typing import Dict, Optional
from datetime import datetime

class StockCache:
    """
    Hash Table (Dictionary) to cache real-time stock prices.
    Provides O(1) lookup for previously fetched prices.
    """
    def __init__(self):
        # The Hash Table mapping ticker -> current_price
        self._cache: Dict[str, float] = {}
        # Track when the price was last updated
        self._last_updated: Dict[str, datetime] = {}

    def get_price(self, ticker: str, force_refresh: bool = False) -> Optional[float]:
        """
        Retrieves the price for a ticker. 
        If force_refresh is True or the ticker is not in cache, fetches from yfinance.
        """
        ticker = ticker.upper()
        
        # O(1) Lookup if we don't need to refresh and it's already cached
        if not force_refresh and ticker in self._cache:
            return self._cache[ticker]
            
        # Fetch from yfinance
        try:
            stock = yf.Ticker(ticker)
            # history(period="1d") is the most robust way to get current/last close price in yfinance
            hist = stock.history(period="1d")
            
            if hist.empty:
                print(f"Warning: Could not fetch data for {ticker}")
                return None
                
            current_price = float(hist['Close'].iloc[-1])
            
            # Save to Hash Table
            self._cache[ticker] = current_price
            self._last_updated[ticker] = datetime.now()
            
            return current_price
            
        except Exception as e:
            print(f"Error fetching price for {ticker}: {e}")
            # Fallback to cache if api fails but we have old data
            return self._cache.get(ticker)
            
    def set_price(self, ticker: str, price: float):
        """
        Manually inject a price into the cache (useful for mock testing or overriding).
        """
        ticker = ticker.upper()
        self._cache[ticker] = price
        self._last_updated[ticker] = datetime.now()

    def get_all_cached_tickers(self) -> list:
        return list(self._cache.keys())
