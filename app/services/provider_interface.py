from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, List, Optional, Any
from app.models.domain import Asset, EquityDetails, HistoricalPrice, MarketMetrics, IncomeStatement, BalanceSheet, CashFlow

class BaseFinancialProvider(ABC):
    """
    Abstract interface for financial data providers.
    Ensures the ETL service is decoupled from the specific data source (e.g. Yahoo Finance, Polygon, etc.).
    """

    @abstractmethod
    def fetch_asset_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetches general asset info. Returns a raw dictionary that will be mapped.
        """
        pass

    @abstractmethod
    def fetch_historical_prices(self, ticker: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        Fetches daily OHLCV historical prices.
        """
        pass

    @abstractmethod
    def fetch_financial_statements(self, ticker: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetches annual and quarterly financials (Income Statement, Balance Sheet, Cash Flow).
        Returns a dictionary with keys: 'income_statement', 'balance_sheet', 'cash_flow',
        each containing a list of dictionaries with raw dates/values.
        """
        pass

    @abstractmethod
    def fetch_market_metrics(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetches current valuation/market metrics (PE, Market Cap, Beta, etc.).
        """
        pass
