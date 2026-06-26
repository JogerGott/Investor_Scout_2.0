from typing import Optional
from app.models.domain import IncomeStatement, BalanceSheet, CashFlow, MarketMetrics, FinancialRatios

class FinancialCalculator:
    """
    State-free service to calculate financial ratios and metrics
    exclusively from stored financial statements and market metrics.
    """

    @staticmethod
    def calculate_ratios(
        id_activo: int,
        income: IncomeStatement,
        balance: BalanceSheet,
        cashflow: CashFlow,
        market_metrics: Optional[MarketMetrics] = None,
        prev_income: Optional[IncomeStatement] = None,
        prev_balance: Optional[BalanceSheet] = None
    ) -> FinancialRatios:
        """
        Calculates all financial ratios for a given period using current statements,
        and optionally YoY statements for growth rates and average assets.
        """
        # 1. Margins
        gross_margin = None
        if income.revenue and income.gross_profit:
            gross_margin = income.gross_profit / income.revenue
        elif income.revenue and income.cost_of_revenue:
            # gross_profit = revenue - cost_of_revenue
            gp = income.revenue - income.cost_of_revenue
            gross_margin = gp / income.revenue

        operating_margin = None
        if income.revenue and income.operating_income:
            operating_margin = income.operating_income / income.revenue

        net_margin = None
        if income.revenue and income.net_income:
            net_margin = income.net_income / income.revenue

        # 2. Liquidity Ratios
        current_ratio = None
        if balance.current_assets and balance.current_liabilities and balance.current_liabilities != 0:
            current_ratio = balance.current_assets / balance.current_liabilities

        quick_ratio = None
        if balance.cash_equivalents and balance.current_liabilities and balance.current_liabilities != 0:
            quick_ratio = balance.cash_equivalents / balance.current_liabilities

        # 3. Leverage
        debt_equity = None
        if balance.total_debt is not None and balance.total_equity and balance.total_equity != 0:
            debt_equity = balance.total_debt / balance.total_equity

        # 4. Profitability: ROE and ROA
        roe = None
        avg_equity = balance.total_equity
        if prev_balance and prev_balance.total_equity and balance.total_equity:
            avg_equity = (balance.total_equity + prev_balance.total_equity) / 2
        if income.net_income and avg_equity and avg_equity != 0:
            roe = income.net_income / avg_equity

        roa = None
        avg_assets = balance.total_assets
        if prev_balance and prev_balance.total_assets and balance.total_assets:
            avg_assets = (balance.total_assets + prev_balance.total_assets) / 2
        if income.net_income and avg_assets and avg_assets != 0:
            roa = income.net_income / avg_assets

        # 5. Asset Turnover
        asset_turnover = None
        if income.revenue and avg_assets and avg_assets != 0:
            asset_turnover = income.revenue / avg_assets

        # 6. Interest Coverage Ratio (ICR)
        icr = None
        if income.operating_income is not None and income.interest_expense and income.interest_expense != 0:
            icr = income.operating_income / income.interest_expense

        # 7. Valuation Yields & Multiples
        fcf_yield = None
        ev_ebitda = None
        if market_metrics:
            if cashflow.free_cash_flow is not None and market_metrics.market_cap and market_metrics.market_cap != 0:
                fcf_yield = cashflow.free_cash_flow / market_metrics.market_cap
            if market_metrics.enterprise_value and income.ebitda and income.ebitda != 0:
                ev_ebitda = market_metrics.enterprise_value / income.ebitda

        # 8. EPS
        eps = None
        if income.net_income and income.shares_outstanding and income.shares_outstanding != 0:
            eps = income.net_income / income.shares_outstanding

        # 9. ROIC
        roic = None
        # Invested Capital = Total Debt + Total Equity - Cash
        if balance.total_debt is not None and balance.total_equity is not None and balance.cash_equivalents is not None:
            invested_capital = balance.total_debt + balance.total_equity - balance.cash_equivalents
            
            # Calculate NOPAT = EBIT * (1 - TaxRate)
            ebit = income.operating_income
            if ebit is not None and ebit != 0:
                tax_rate = 0.21  # Fallback to standard 21% tax rate
                if income.tax_expense is not None and income.tax_expense >= 0:
                    # Calculate actual tax rate
                    tax_rate = income.tax_expense / ebit
                    if tax_rate < 0 or tax_rate > 1:
                        tax_rate = 0.21  # sanity check bound
                        
                nopat = ebit * (1 - tax_rate)
                if invested_capital and invested_capital != 0:
                    roic = nopat / invested_capital

        # 10. Growth Rates (YoY)
        revenue_growth = None
        if prev_income and prev_income.revenue and income.revenue:
            revenue_growth = (income.revenue - prev_income.revenue) / prev_income.revenue

        eps_growth = None
        if prev_income and income.net_income and income.shares_outstanding and prev_income.net_income and prev_income.shares_outstanding:
            prev_eps = prev_income.net_income / prev_income.shares_outstanding
            curr_eps = income.net_income / income.shares_outstanding
            if prev_eps != 0:
                eps_growth = (curr_eps - prev_eps) / prev_eps

        return FinancialRatios(
            id_activo=id_activo,
            periodo=income.periodo,
            fecha_reporte=income.fecha_reporte,
            roe=roe,
            roa=roa,
            roic=roic,
            ev_ebitda=ev_ebitda,
            gross_margin=gross_margin,
            operating_margin=operating_margin,
            net_margin=net_margin,
            quick_ratio=quick_ratio,
            current_ratio=current_ratio,
            debt_equity=debt_equity,
            icr=icr,
            asset_turnover=asset_turnover,
            eps=eps,
            eps_growth=eps_growth,
            revenue_growth=revenue_growth,
            fcf_yield=fcf_yield
        )
