import math
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from app.models.domain import Asset, EquityDetails, HistoricalPrice, MarketMetrics, IncomeStatement, BalanceSheet, CashFlow, FinancialRatios

class FinancialMapper:
    """
    Maps raw provider responses to internal domain DTOs.
    Converts data types, dates, cleans values, and maps field synonyms.
    """

    @staticmethod
    def _clean_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            val = float(value)
            if math.isnan(val) or math.isinf(val):
                return None
            return val
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _clean_int(value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            val = float(value) # Handle '12345.0'
            if math.isnan(val) or math.isinf(val):
                return None
            return int(val)
        except (ValueError, TypeError):
            return None

    @classmethod
    def _extract_field(cls, row: Dict[str, Any], synonyms: List[str]) -> Optional[Any]:
        for syn in synonyms:
            # Check case-insensitive
            syn_lower = syn.lower()
            for k, v in row.items():
                if str(k).lower() == syn_lower:
                    return v
        return None

    @classmethod
    def determine_period(cls, report_date: date, is_quarterly: bool) -> str:
        """
        Maps a report date to standard periods like 'FY 2023' or 'Q1 2024'.
        """
        year = report_date.year
        if not is_quarterly:
            return f"FY {year}"
        
        month = report_date.month
        if month in [1, 2, 3]:
            return f"Q1 {year}"
        elif month in [4, 5, 6]:
            return f"Q2 {year}"
        elif month in [7, 8, 9]:
            return f"Q3 {year}"
        else:
            return f"Q4 {year}"

    @classmethod
    def to_asset(cls, raw: Dict[str, Any]) -> Asset:
        return Asset(
            ticker=raw["ticker"],
            nombre=raw.get("nombre") or raw.get("longName") or raw["ticker"],
            tipo_activo=raw.get("tipo_activo", "EQUITY"),
            moneda=raw.get("moneda", "USD"),
            exchange=raw.get("exchange"),
            pais=raw.get("pais")
        )

    @classmethod
    def to_equity_details(cls, id_activo: int, raw: Dict[str, Any]) -> EquityDetails:
        earnings_date_raw = raw.get("earnings_date")
        earnings_date = None
        if earnings_date_raw:
            if isinstance(earnings_date_raw, (date, datetime)):
                earnings_date = earnings_date_raw if isinstance(earnings_date_raw, date) else earnings_date_raw.date()
            elif isinstance(earnings_date_raw, int):
                # Timestamp
                earnings_date = datetime.fromtimestamp(earnings_date_raw).date()
            elif isinstance(earnings_date_raw, str):
                try:
                    # Try common parse formats
                    earnings_date = datetime.strptime(earnings_date_raw.split("T")[0], "%Y-%m-%d").date()
                except ValueError:
                    pass
        
        return EquityDetails(
            id_activo=id_activo,
            sector=raw.get("sector"),
            industria=raw.get("industria"),
            earnings_date=earnings_date
        )

    @classmethod
    def to_historical_price(cls, id_activo: int, raw: Dict[str, Any]) -> HistoricalPrice:
        return HistoricalPrice(
            id_activo=id_activo,
            fecha=raw["fecha"],
            open_price=cls._clean_float(raw.get("open_price")),
            high_price=cls._clean_float(raw.get("high_price")),
            low_price=cls._clean_float(raw.get("low_price")),
            close_price=cls._clean_float(raw.get("close_price")) or 0.0,
            adjust_close=cls._clean_float(raw.get("adjust_close")) or 0.0,
            volumen=cls._clean_int(raw.get("volumen"))
        )

    @classmethod
    def to_market_metrics(cls, id_activo: int, raw: Dict[str, Any]) -> MarketMetrics:
        return MarketMetrics(
            id_activo=id_activo,
            fecha=raw.get("fecha", date.today()),
            precio=cls._clean_float(raw.get("precio")),
            market_cap=cls._clean_int(raw.get("market_cap")),
            enterprise_value=cls._clean_int(raw.get("enterprise_value")),
            pe_ratio=cls._clean_float(raw.get("pe_ratio")),
            pe_forward=cls._clean_float(raw.get("pe_forward")),
            pb_ratio=cls._clean_float(raw.get("pb_ratio")),
            ps_ratio=cls._clean_float(raw.get("ps_ratio")),
            peg=cls._clean_float(raw.get("peg")),
            beta=cls._clean_float(raw.get("beta")),
            dividend_yield=cls._clean_float(raw.get("dividend_yield"))
        )

    @classmethod
    def to_income_statement(cls, id_activo: int, raw: Dict[str, Any], is_quarterly: bool) -> IncomeStatement:
        report_date = raw["report_date"]
        periodo = cls.determine_period(report_date, is_quarterly)
        
        revenue = cls._clean_float(cls._extract_field(raw, ['Total Revenue', 'Revenue', 'Operating Revenue']))
        cost_of_revenue = cls._clean_float(cls._extract_field(raw, ['Cost Of Revenue', 'Cost of Goods Sold', 'COGS']))
        gross_profit = cls._clean_float(cls._extract_field(raw, ['Gross Profit']))
        operating_expenses = cls._clean_float(cls._extract_field(raw, ['Total Operating Expenses', 'Operating Expense', 'Operating Expenses']))
        operating_income = cls._clean_float(cls._extract_field(raw, ['Operating Income', 'EBIT', 'Operating Income or Loss']))
        net_income = cls._clean_float(cls._extract_field(raw, ['Net Income', 'Net Income Common Stockholders', 'Net Income from Continuing Ops']))
        ebitda = cls._clean_float(cls._extract_field(raw, ['EBITDA', 'Normalized EBITDA']))
        shares_outstanding = cls._clean_int(cls._extract_field(raw, ['Implied Shares Outstanding', 'Basic Shares Outstanding', 'Weighted Average Shares']))
        interest_expense = cls._clean_float(cls._extract_field(raw, ['Interest Expense', 'Interest Expense Non Operating', 'Total Interest Expense']))
        tax_expense = cls._clean_float(cls._extract_field(raw, ['Tax Provision', 'Income Tax Provision', 'Tax Expense']))
        
        return IncomeStatement(
            id_activo=id_activo,
            periodo=periodo,
            fecha_reporte=report_date,
            revenue=revenue,
            cost_of_revenue=cost_of_revenue,
            gross_profit=gross_profit,
            operating_expenses=operating_expenses,
            operating_income=operating_income,
            net_income=net_income,
            ebitda=ebitda,
            shares_outstanding=shares_outstanding,
            interest_expense=interest_expense,
            tax_expense=tax_expense
        )

    @classmethod
    def to_balance_sheet(cls, id_activo: int, raw: Dict[str, Any], is_quarterly: bool) -> BalanceSheet:
        report_date = raw["report_date"]
        periodo = cls.determine_period(report_date, is_quarterly)
        
        total_assets = cls._clean_float(cls._extract_field(raw, ['Total Assets']))
        total_liabilities = cls._clean_float(cls._extract_field(raw, ['Total Liabilities', 'Total Liabilities Net Min Interest']))
        total_equity = cls._clean_float(cls._extract_field(raw, ['Stockholders Equity', 'Total Equity Gross Minority Interest', 'Common Stock Equity']))
        total_debt = cls._clean_float(cls._extract_field(raw, ['Total Debt', 'Long Term Debt + Current Debt', 'Total Debt Capital']))
        cash_equivalents = cls._clean_float(cls._extract_field(raw, ['Cash Cash Equivalents And Short Term Investments', 'Cash And Cash Equivalents', 'Cash']))
        current_assets = cls._clean_float(cls._extract_field(raw, ['Total Current Assets', 'Current Assets']))
        current_liabilities = cls._clean_float(cls._extract_field(raw, ['Total Current Liabilities', 'Current Liabilities']))
        
        # Fallback for Total Debt if missing
        if total_debt is None:
            # Try summing short and long term debt if available in raw keys
            std = cls._clean_float(cls._extract_field(raw, ['Current Debt', 'Short Term Debt'])) or 0.0
            ltd = cls._clean_float(cls._extract_field(raw, ['Long Term Debt'])) or 0.0
            if std > 0 or ltd > 0:
                total_debt = std + ltd
                
        return BalanceSheet(
            id_activo=id_activo,
            periodo=periodo,
            fecha_reporte=report_date,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            total_equity=total_equity,
            total_debt=total_debt,
            cash_equivalents=cash_equivalents,
            current_assets=current_assets,
            current_liabilities=current_liabilities
        )

    @classmethod
    def to_cash_flow(cls, id_activo: int, raw: Dict[str, Any], is_quarterly: bool) -> CashFlow:
        report_date = raw["report_date"]
        periodo = cls.determine_period(report_date, is_quarterly)
        
        operating_cf = cls._clean_float(cls._extract_field(raw, ['Operating Cash Flow', 'Cash Flow From Operating Activities', 'Net Cash From Operating Activities']))
        investing_cf = cls._clean_float(cls._extract_field(raw, ['Investing Cash Flow', 'Cash Flow From Investing Activities', 'Net Cash From Investing Activities']))
        financing_cf = cls._clean_float(cls._extract_field(raw, ['Financing Cash Flow', 'Cash Flow From Financing Activities', 'Net Cash From Financing Activities']))
        free_cash_flow = cls._clean_float(cls._extract_field(raw, ['Free Cash Flow']))
        capex = cls._clean_float(cls._extract_field(raw, ['Capital Expenditure', 'CapEx', 'Purchase of Property Plant and Equipment']))
        
        # Capital Expenditure is usually negative in yfinance, let's keep it positive for standardization
        if capex is not None:
            capex = abs(capex)
            
        if free_cash_flow is None and operating_cf is not None and capex is not None:
            free_cash_flow = operating_cf - capex
            
        return CashFlow(
            id_activo=id_activo,
            periodo=periodo,
            fecha_reporte=report_date,
            operating_cf=operating_cf,
            investing_cf=investing_cf,
            financing_cf=financing_cf,
            free_cash_flow=free_cash_flow,
            capex=capex
        )
