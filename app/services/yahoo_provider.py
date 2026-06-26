import time
import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Any
import yfinance as yf
from app.services.provider_interface import BaseFinancialProvider

logger = logging.getLogger(__name__)

class YahooFinanceProvider(BaseFinancialProvider):
    """
    Yahoo Finance provider implementing the BaseFinancialProvider interface.
    Fetches data using yfinance, handles retries, and extracts raw data.
    """
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def _execute_with_retry(self, func, *args, **kwargs) -> Any:
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                wait_time = self.backoff_factor ** attempt
                logger.warning(f"YahooFinance API call failed (attempt {attempt + 1}/{self.max_retries}): {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
        logger.error(f"YahooFinance API call failed after {self.max_retries} attempts.")
        if last_error is None:
            raise RuntimeError("YahooFinance API call failed with no exception recorded.")
        raise last_error

    def fetch_asset_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        ticker = ticker.upper()
        try:
            ticker_obj = yf.Ticker(ticker)
            info = self._execute_with_retry(lambda: ticker_obj.info)
            if not info or 'longName' not in info:
                # Try fetching fundamental info via fastinfo
                fast_info = ticker_obj.fast_info
                return {
                    "ticker": ticker,
                    "nombre": ticker,
                    "tipo_activo": "EQUITY",
                    "moneda": getattr(fast_info, 'currency', 'USD'),
                    "exchange": getattr(fast_info, 'exchange', None),
                    "pais": None,
                    "timezone": getattr(fast_info, 'timezone', None)
                }
            return {
                "ticker": ticker,
                "nombre": info.get("longName") or info.get("shortName") or ticker,
                "tipo_activo": "EQUITY" if info.get("quoteType", "EQUITY") == "EQUITY" else "BOND",
                "moneda": info.get("currency", "USD"),
                "exchange": info.get("exchange"),
                "pais": info.get("country"),
                "timezone": info.get("timeZoneShortName"),
                "sector": info.get("sector"),
                "industria": info.get("industry"),
                "earnings_date": info.get("nextEarningsDate"),
                "isin": info.get("isin")
            }
        except Exception as e:
            logger.error(f"Error fetching asset info for {ticker}: {e}")
            return None

    def fetch_historical_prices(self, ticker: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        ticker = ticker.upper()
        try:
            ticker_obj = yf.Ticker(ticker)
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            
            df = self._execute_with_retry(
                lambda: ticker_obj.history(start=start_str, end=end_str, interval="1d")
            )
            
            prices = []
            for dt, row in df.iterrows():
                # Extract close and adjusted close
                close = float(row.get("Close", 0.0))
                # yfinance returns adjusted close as Close if auto_adjust is True (default)
                # but we will try to get 'Adj Close' or default to Close
                adj_close = float(row.get("Adj Close", close))
                
                prices.append({
                    "fecha": dt.date() if hasattr(dt, 'date') else dt,
                    "open_price": float(row.get("Open", 0.0)),
                    "high_price": float(row.get("High", 0.0)),
                    "low_price": float(row.get("Low", 0.0)),
                    "close_price": close,
                    "adjust_close": adj_close,
                    "volumen": int(row.get("Volume", 0))
                })
            return prices
        except Exception as e:
            logger.error(f"Error fetching historical prices for {ticker}: {e}")
            return []

    def _convert_df_to_list(self, df) -> List[Dict[str, Any]]:
        if df is None or df.empty:
            return []
        
        results = []
        df_transposed = df.T
        for dt, row in df_transposed.iterrows():
            row_dict = row.to_dict()
            # Clean up keys for easier matching later
            cleaned_row = {str(k).strip().lower(): v for k, v in row_dict.items() if v is not None}
            # Keep original keys as well
            for k, v in row_dict.items():
                cleaned_row[str(k)] = v
                
            report_date = dt.date() if hasattr(dt, 'date') else dt
            cleaned_row["report_date"] = report_date
            results.append(cleaned_row)
            
        return results

    def fetch_financial_statements(self, ticker: str) -> Dict[str, List[Dict[str, Any]]]:
        ticker = ticker.upper()
        try:
            ticker_obj = yf.Ticker(ticker)
            
            # Fetch annuals
            annual_income = self._execute_with_retry(lambda: ticker_obj.financials)
            annual_balance = self._execute_with_retry(lambda: ticker_obj.balance_sheet)
            annual_cashflow = self._execute_with_retry(lambda: ticker_obj.cashflow)
            
            # Fetch quarterlys
            quarterly_income = self._execute_with_retry(lambda: ticker_obj.quarterly_financials)
            quarterly_balance = self._execute_with_retry(lambda: ticker_obj.quarterly_balance_sheet)
            quarterly_cashflow = self._execute_with_retry(lambda: ticker_obj.quarterly_cashflow)
            
            return {
                "annual_income": self._convert_df_to_list(annual_income),
                "annual_balance": self._convert_df_to_list(annual_balance),
                "annual_cashflow": self._convert_df_to_list(annual_cashflow),
                "quarterly_income": self._convert_df_to_list(quarterly_income),
                "quarterly_balance": self._convert_df_to_list(quarterly_balance),
                "quarterly_cashflow": self._convert_df_to_list(quarterly_cashflow),
            }
        except Exception as e:
            logger.error(f"Error fetching financial statements for {ticker}: {e}")
            return {
                "annual_income": [],
                "annual_balance": [],
                "annual_cashflow": [],
                "quarterly_income": [],
                "quarterly_balance": [],
                "quarterly_cashflow": [],
            }

    def fetch_market_metrics(self, ticker: str) -> Optional[Dict[str, Any]]:
        ticker = ticker.upper()
        try:
            ticker_obj = yf.Ticker(ticker)
            info = self._execute_with_retry(lambda: ticker_obj.info)
            if not info:
                # Try fetching basic price using history
                hist = ticker_obj.history(period="1d")
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
                    return {
                        "fecha": date.today(),
                        "precio": current_price
                    }
                return None
                
            # yfinance info dict mapping
            return {
                "fecha": date.today(),
                "precio": info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose"),
                "market_cap": info.get("marketCap"),
                "enterprise_value": info.get("enterpriseValue"),
                "pe_ratio": info.get("trailingPE"),
                "pe_forward": info.get("forwardPE"),
                "pb_ratio": info.get("priceToBook"),
                "ps_ratio": info.get("priceToSalesTrailing12Months"),
                "peg": info.get("pegRatio"),
                "beta": info.get("beta"),
                "dividend_yield": info.get("dividendYield")
            }
        except Exception as e:
            logger.error(f"Error fetching market metrics for {ticker}: {e}")
            return None
