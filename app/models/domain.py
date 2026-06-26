from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List

@dataclass
class Asset:
    ticker: str
    nombre: str
    tipo_activo: str  # 'EQUITY' or 'BOND'
    moneda: str = "USD"
    exchange: Optional[str] = None
    pais: Optional[str] = None
    id_activo: Optional[int] = None

    def __post_init__(self):
        self.ticker = self.ticker.upper()
        self.tipo_activo = self.tipo_activo.upper()

@dataclass
class EquityDetails:
    id_activo: int
    sector: Optional[str] = None
    industria: Optional[str] = None
    earnings_date: Optional[date] = None

@dataclass
class BondDetails:
    id_activo: int
    fecha_maduracion: Optional[date] = None
    tasa_cupon: Optional[float] = None
    frecuencia_pago: Optional[str] = None  # 'MENSUAL', 'TRIMESTRAL', 'SEMESTRAL', 'ANUAL'
    valor_nominal: Optional[float] = None
    calificacion: Optional[str] = None
    emisor: str = "SOBERANO"  # 'SOBERANO' or 'CORPORATIVO'

@dataclass
class HistoricalPrice:
    id_activo: int
    fecha: date
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    close_price: float = 0.0
    adjust_close: float = 0.0
    volumen: Optional[int] = None

@dataclass
class MarketMetrics:
    id_activo: int
    fecha: date
    precio: Optional[float] = None
    market_cap: Optional[int] = None
    enterprise_value: Optional[int] = None
    pe_ratio: Optional[float] = None
    pe_forward: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    peg: Optional[float] = None
    beta: Optional[float] = None
    dividend_yield: Optional[float] = None
    id_metricas: Optional[int] = None

@dataclass
class IncomeStatement:
    id_activo: int
    periodo: str  # e.g., 'Q1 2024', 'FY 2023'
    fecha_reporte: date
    revenue: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_expenses: Optional[float] = None
    operating_income: Optional[float] = None  # EBIT
    net_income: Optional[float] = None
    ebitda: Optional[float] = None
    shares_outstanding: Optional[int] = None
    interest_expense: Optional[float] = None  # Schema Extension
    tax_expense: Optional[float] = None       # Schema Extension
    id_statement: Optional[int] = None

@dataclass
class BalanceSheet:
    id_activo: int
    periodo: str
    fecha_reporte: date
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    total_debt: Optional[float] = None
    cash_equivalents: Optional[float] = None
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None
    id_balance: Optional[int] = None

@dataclass
class CashFlow:
    id_activo: int
    periodo: str
    fecha_reporte: date
    operating_cf: Optional[float] = None
    investing_cf: Optional[float] = None
    financing_cf: Optional[float] = None
    free_cash_flow: Optional[float] = None
    capex: Optional[float] = None
    id_cashflow: Optional[int] = None

@dataclass
class FinancialRatios:
    id_activo: int
    periodo: str
    fecha_reporte: date
    roe: Optional[float] = None
    roa: Optional[float] = None
    roic: Optional[float] = None
    ev_ebitda: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    quick_ratio: Optional[float] = None
    current_ratio: Optional[float] = None
    debt_equity: Optional[float] = None
    icr: Optional[float] = None
    asset_turnover: Optional[float] = None
    eps: Optional[float] = None
    eps_growth: Optional[float] = None
    revenue_growth: Optional[float] = None
    fcf_yield: Optional[float] = None
    id_ratio: Optional[int] = None
