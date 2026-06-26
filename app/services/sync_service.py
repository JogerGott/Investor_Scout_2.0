import logging
import time
from datetime import date, timedelta
from typing import Dict, List, Optional, Any

from app.models.domain import Asset, EquityDetails, HistoricalPrice, MarketMetrics, IncomeStatement, BalanceSheet, CashFlow, FinancialRatios
from app.services.provider_interface import BaseFinancialProvider
from app.services.mapper import FinancialMapper
from app.services.calculator import FinancialCalculator
from app.data_structures.stock_cache import StockCache

from app.repositories.activo_repository import ActivoRepository
from app.repositories.equity_repository import EquityRepository
from app.repositories.historico_repository import HistoricoRepository
from app.repositories.metrics_repository import MetricsRepository
from app.repositories.income_repository import IncomeRepository
from app.repositories.balance_repository import BalanceRepository
from app.repositories.cash_flow_repository import CashFlowRepository
from app.repositories.ratios_repository import RatiosRepository

logger = logging.getLogger(__name__)

class SyncService:
    """
    Orchestrates the ETL (Extract, Transform, Load) synchronization pipeline.
    Connects data providers with repositories, runs calculations, and updates StockCache.
    """
    def __init__(self, provider: BaseFinancialProvider, stock_cache: Optional[StockCache] = None):
        self.provider = provider
        self.stock_cache = stock_cache if stock_cache else StockCache()
        
        # Instantiate repositories
        self.activo_repo = ActivoRepository()
        self.equity_repo = EquityRepository()
        self.historico_repo = HistoricoRepository()
        self.metrics_repo = MetricsRepository()
        self.income_repo = IncomeRepository()
        self.balance_repo = BalanceRepository()
        self.cash_flow_repo = CashFlowRepository()
        self.ratios_repo = RatiosRepository()

    def _get_or_create_asset(self, ticker: str) -> Asset:
        """
        Retrieves the asset from database, or downloads and creates it if it doesn't exist.
        """
        ticker = ticker.upper()
        asset = self.activo_repo.get_by_ticker(ticker)
        if asset:
            return asset
            
        logger.info(f"Asset for ticker {ticker} not found in DB. Performing extraction...")
        raw_info = self.provider.fetch_asset_info(ticker)
        if not raw_info:
            raise ValueError(f"Could not fetch asset info for ticker '{ticker}' from provider.")
            
        asset = FinancialMapper.to_asset(raw_info)
        id_activo = self.activo_repo.save(asset)
        asset.id_activo = id_activo
        
        if asset.tipo_activo == "EQUITY":
            equity_details = FinancialMapper.to_equity_details(id_activo, raw_info)
            self.equity_repo.save(equity_details)
            
        logger.info(f"Successfully created asset '{asset.nombre}' with ID {id_activo} in DB.")
        return asset

    def _get_yoy_period(self, period: str) -> Optional[str]:
        parts = period.split()
        if len(parts) == 2:
            prefix, year_str = parts
            try:
                prev_year = int(year_str) - 1
                return f"{prefix} {prev_year}"
            except ValueError:
                pass
        return None

    def sync_initial(self, ticker: str):
        """
        Runs the full initial sync, downloading 5 years of price history and 4 years of financials.
        """
        ticker = ticker.upper()
        start_time = time.time()
        logger.info(f"Starting initial sync for {ticker}...")
        
        inserted_count = 0
        updated_count = 0
        
        try:
            # 1. Get or create asset
            asset = self._get_or_create_asset(ticker)
            id_activo = asset.id_activo
            
            # 2. Sync historical prices (5 years)
            end_date = date.today()
            start_date = end_date - timedelta(days=5*365)
            logger.info(f"Fetching 5-year historical prices for {ticker}...")
            raw_prices = self.provider.fetch_historical_prices(ticker, start_date, end_date)
            
            prices = [FinancialMapper.to_historical_price(id_activo, p) for p in raw_prices]
            self.historico_repo.save_bulk(prices)
            inserted_count += len(prices)
            logger.info(f"Saved {len(prices)} price bars to DB.")
            
            # 3. Sync financials
            logger.info(f"Fetching financial statements for {ticker}...")
            raw_statements = self.provider.fetch_financial_statements(ticker)
            
            # Group annual and quarterly statement rows
            statement_groups = [
                ("annual_income", "annual_balance", "annual_cashflow", False),
                ("quarterly_income", "quarterly_balance", "quarterly_cashflow", True)
            ]
            
            for inc_key, bal_key, cf_key, is_quarterly in statement_groups:
                income_list = [FinancialMapper.to_income_statement(id_activo, r, is_quarterly) for r in raw_statements[inc_key]]
                balance_list = [FinancialMapper.to_balance_sheet(id_activo, r, is_quarterly) for r in raw_statements[bal_key]]
                cf_list = [FinancialMapper.to_cash_flow(id_activo, r, is_quarterly) for r in raw_statements[cf_key]]
                
                # Save financials
                for inc in income_list:
                    self.income_repo.save(inc)
                    inserted_count += 1
                for bal in balance_list:
                    self.balance_repo.save(bal)
                    inserted_count += 1
                for cf in cf_list:
                    self.cash_flow_repo.save(cf)
                    inserted_count += 1
                
                # Run derived ratio calculations
                # For YoY references, let's create a map of loaded/historical statements
                income_map = {inc.periodo: inc for inc in income_list}
                balance_map = {bal.periodo: bal for bal in balance_list}
                cf_map = {cf.periodo: cf for cf in cf_list}
                
                # Fetch latest market metrics for yield calculation if available
                market_metrics = self.provider.fetch_market_metrics(ticker)
                metrics_dto = None
                if market_metrics:
                    metrics_dto = FinancialMapper.to_market_metrics(id_activo, market_metrics)
                
                for period, inc in income_map.items():
                    bal = balance_map.get(period)
                    cf = cf_map.get(period)
                    if bal and cf:
                        # Find YoY statements
                        yoy_period = self._get_yoy_period(period)
                        prev_inc = None
                        prev_bal = None
                        
                        if yoy_period:
                            # Try in-memory first
                            prev_inc = income_map.get(yoy_period)
                            prev_bal = balance_map.get(yoy_period)
                            
                            # Fallback to DB query
                            if not prev_inc:
                                prev_inc = self.income_repo.get_statement(id_activo, yoy_period)
                            if not prev_bal:
                                prev_bal = self.balance_repo.get_statement(id_activo, yoy_period)
                        
                        ratios = FinancialCalculator.calculate_ratios(
                            id_activo=id_activo,
                            income=inc,
                            balance=bal,
                            cashflow=cf,
                            market_metrics=metrics_dto,
                            prev_income=prev_inc,
                            prev_balance=prev_bal
                        )
                        self.ratios_repo.save(ratios)
                        inserted_count += 1
                        
            # 4. Sync current market metrics
            logger.info(f"Fetching current market metrics for {ticker}...")
            raw_metrics = self.provider.fetch_market_metrics(ticker)
            if raw_metrics:
                metrics = FinancialMapper.to_market_metrics(id_activo, raw_metrics)
                self.metrics_repo.save(metrics)
                inserted_count += 1
                
                # Synchronize stock cache
                if metrics.precio:
                    self.stock_cache.set_price(ticker, metrics.precio)
                    
            elapsed = time.time() - start_time
            logger.info(f"Completed initial sync for {ticker} in {elapsed:.2f}s. Loaded {inserted_count} records.")
            return True
            
        except Exception as e:
            logger.error(f"Failed initial sync for {ticker}: {e}", exc_info=True)
            return False

    def sync_daily(self, ticker: str):
        """
        Runs the daily sync: fetches current price, updates market metrics, and fetches recent history.
        """
        ticker = ticker.upper()
        start_time = time.time()
        logger.info(f"Starting daily sync for {ticker}...")
        
        inserted_count = 0
        
        try:
            asset = self._get_or_create_asset(ticker)
            id_activo = asset.id_activo
            
            # 1. Fetch current price and market metrics
            raw_metrics = self.provider.fetch_market_metrics(ticker)
            if raw_metrics:
                metrics = FinancialMapper.to_market_metrics(id_activo, raw_metrics)
                self.metrics_repo.save(metrics)
                inserted_count += 1
                
                if metrics.precio:
                    self.stock_cache.set_price(ticker, metrics.precio)
                    
            # 2. Fetch last 7 days of price history to bridge any gaps (weekends, holidays)
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
            raw_prices = self.provider.fetch_historical_prices(ticker, start_date, end_date)
            prices = [FinancialMapper.to_historical_price(id_activo, p) for p in raw_prices]
            self.historico_repo.save_bulk(prices)
            inserted_count += len(prices)
            
            elapsed = time.time() - start_time
            logger.info(f"Completed daily sync for {ticker} in {elapsed:.2f}s. Updated {inserted_count} records.")
            return True
            
        except Exception as e:
            logger.error(f"Failed daily sync for {ticker}: {e}")
            return False

    def sync_quarterly(self, ticker: str):
        """
        Runs the quarterly sync: fetches financial statements, calculates new ratios.
        """
        ticker = ticker.upper()
        start_time = time.time()
        logger.info(f"Starting quarterly sync for {ticker}...")
        
        inserted_count = 0
        
        try:
            asset = self._get_or_create_asset(ticker)
            id_activo = asset.id_activo
            
            # Fetch financials
            raw_statements = self.provider.fetch_financial_statements(ticker)
            
            statement_groups = [
                ("annual_income", "annual_balance", "annual_cashflow", False),
                ("quarterly_income", "quarterly_balance", "quarterly_cashflow", True)
            ]
            
            # Load current market metrics for FCF yield
            raw_metrics = self.provider.fetch_market_metrics(ticker)
            metrics_dto = None
            if raw_metrics:
                metrics_dto = FinancialMapper.to_market_metrics(id_activo, raw_metrics)
            
            for inc_key, bal_key, cf_key, is_quarterly in statement_groups:
                income_list = [FinancialMapper.to_income_statement(id_activo, r, is_quarterly) for r in raw_statements[inc_key]]
                balance_list = [FinancialMapper.to_balance_sheet(id_activo, r, is_quarterly) for r in raw_statements[bal_key]]
                cf_list = [FinancialMapper.to_cash_flow(id_activo, r, is_quarterly) for r in raw_statements[cf_key]]
                
                income_map = {inc.periodo: inc for inc in income_list}
                balance_map = {bal.periodo: bal for bal in balance_list}
                cf_map = {cf.periodo: cf for cf in cf_list}
                
                for period, inc in income_map.items():
                    bal = balance_map.get(period)
                    cf = cf_map.get(period)
                    
                    if bal and cf:
                        # Save statements (will ignore/update duplicates)
                        self.income_repo.save(inc)
                        self.balance_repo.save(bal)
                        self.cash_flow_repo.save(cf)
                        inserted_count += 3
                        
                        # Find YoY statements for growth/avg formulas
                        yoy_period = self._get_yoy_period(period)
                        prev_inc = None
                        prev_bal = None
                        
                        if yoy_period:
                            prev_inc = income_map.get(yoy_period) or self.income_repo.get_statement(id_activo, yoy_period)
                            prev_bal = balance_map.get(yoy_period) or self.balance_repo.get_statement(id_activo, yoy_period)
                            
                        ratios = FinancialCalculator.calculate_ratios(
                            id_activo=id_activo,
                            income=inc,
                            balance=bal,
                            cashflow=cf,
                            market_metrics=metrics_dto,
                            prev_income=prev_inc,
                            prev_balance=prev_bal
                        )
                        self.ratios_repo.save(ratios)
                        inserted_count += 1
                        
            elapsed = time.time() - start_time
            logger.info(f"Completed quarterly sync for {ticker} in {elapsed:.2f}s. Loaded/updated {inserted_count} statements & ratios.")
            return True
            
        except Exception as e:
            logger.error(f"Failed quarterly sync for {ticker}: {e}")
            return False
