from datetime import datetime
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.company import Company
from app.data_structures.stock_cache import StockCache
from app.data_structures.portfolio_tree import PortfolioRootNode, SectorNode, CompanyNode
from app.data_structures.company_graph import CompanyRelationshipGraph
import time
from app.data_structures.stock_cache import StockCache
import time

def run_simulation():
    print("--- Investor Scout: M.V.P Initial Simulation ---")
    
    # 1. Create a User
    user = User(
        user_id=1, 
        first_name="Joger", 
        last_name="Munoz", 
        email="joger@investorscout.com", 
        password_hash="***", 
    )
    
    print(f"\nUser created: {user.first_name} {user.last_name}")

    # 2. Create the qualitative Company Profile (Won't change often)
    aapl_company = Company(
        ticker="AAPL",
        name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        moat="Brand loyalty, Ecosystem lock-in",
        business_model="Premium hardware integrated with high-margin services",
        company_stage="Value"
    )
    print(f"\nCompany Profile: {aapl_company.name} | Sector: {aapl_company.sector} | Moat: {aapl_company.moat}")
    
    # 3. Create a Portfolio structure
    portfolio = Portfolio(
        portfolio_id=1,
        user_id=user.user_id,
        name="Value Investing Portfolio",
        cash_balance=10000.0
    )
    user.portfolios.append(portfolio)
    print(f"\nPortfolio initialized: '{portfolio.name}' with Cash: ${portfolio.cash_balance:.2f}")

    # 4. Simulate the Immutable Transaction Log via LinkedList
    print("\nExecuting Transactions...")
    
    portfolio.add_transaction(ticker="AAPL", trans_type="BUY", shares=10, price=150.0, date=datetime.now())
    print(f" -> BUY 10 AAPL @ $150.0")
    
    portfolio.add_transaction(ticker="NVDA", trans_type="BUY", shares=5, price=400.0, date=datetime.now())
    print(f" -> BUY 5 NVDA @ $400.0")
    
    portfolio.add_transaction(ticker="AAPL", trans_type="SELL", shares=5, price=180.0, date=datetime.now())
    print(f" -> SELL 5 AAPL @ $180.0")
    
    # 5. Display the State computed implicitly by the Linked List
    print("\n--- Current Holdings (Calculated from Transaction Log) ---")
    for ticker, holding in portfolio.holdings.items():
        print(f"Holding: {holding.ticker} | Shares: {holding.shares} | Avg Cost Basis: ${holding.avg_cost:.2f}")

    print(f"\nRemaining Cash Balance: ${portfolio.cash_balance:.2f}")

def test_stock_cache():
    print("\n--- Testing StockCache Hash Table ---")
    cache = StockCache()
    
    print("1. Fetching AAPL from API (Expect delay...)")
    start = time.time()
    price = cache.get_price("AAPL")
    if price:
        print(f" -> AAPL Price: ${price:.2f} (Took {time.time() - start:.4f}s)")
    
    print("\n2. Fetching AAPL again from Cache (O(1) lookup...)")
    start = time.time()
    price_cached = cache.get_price("AAPL")
    if price_cached:
        print(f" -> AAPL Price: ${price_cached:.2f} (Took {time.time() - start:.4f}s)")
    
    print("\n3. Fetching MSFT with force_refresh=True (Expect delay...)")
    start = time.time()
    price_msft = cache.get_price("MSFT", force_refresh=True)
    if price_msft:
        print(f" -> MSFT Price: ${price_msft:.2f} (Took {time.time() - start:.4f}s)")
    
    print("\n3. Fetching ADBE with force_refresh=True (Expect delay...)")
    start = time.time()
    price_msft = cache.get_price("ADBE", force_refresh=True)
    if price_msft:
        print(f" -> ADBE Price: ${price_msft:.2f} (Took {time.time() - start:.4f}s)")

    print(f"\nAll cached tickers: {cache.get_all_cached_tickers()}")

def test_portfolio_tree():
    print("\n--- Testing PortfolioTree (Recursive Valuation) ---")
    
    # Create the root portfolio
    root = PortfolioRootNode(name="My Value Portfolio", cash_balance=5000.0)
    
    # Create Sector nodes
    tech_sector = SectorNode("Technology")
    finance_sector = SectorNode("Financials")
    
    # Add sectors to root
    root.add_child(tech_sector)
    root.add_child(finance_sector)
    
    # Add Company leaf nodes
    # AAPL and MSFT in Tech
    aapl_node = CompanyNode(ticker="AAPL", shares=10, current_price=150.0) # $1500
    msft_node = CompanyNode(ticker="MSFT", shares=5, current_price=400.0)  # $2000
    tech_sector.add_child(aapl_node)
    tech_sector.add_child(msft_node)
    
    # JPM in Finance
    jpm_node = CompanyNode(ticker="JPM", shares=20, current_price=190.0)   # $3800
    finance_sector.add_child(jpm_node)
    
    # Calculate Total Value (Should be 5000 + 1500 + 2000 + 3800 = 12300)
    print("Tree Hierarchy and Values:")
    root.display()
    print(f"\nTotal Portfolio Calculated Value: ${root.get_value():.2f}")

def test_company_graph():
    print("\n--- Testing CompanyRelationshipGraph (Risk Exposure) ---")
    
    graph = CompanyRelationshipGraph()
    
    # Define relationships (Fase 1 manual input)
    # TSM is a supplier to NVDA and AAPL
    graph.add_relationship("NVDA", "TSM", "SUPPLIER")
    graph.add_relationship("AAPL", "TSM", "SUPPLIER")
    
    # MSFT is a customer of NVDA
    graph.add_relationship("MSFT", "NVDA", "CUSTOMER")
    
    # NVDA and AMD are competitors
    graph.add_bidirectional_relationship("NVDA", "AMD", "COMPETITOR")
    
    print("Graph Structure:")
    graph.display_graph()
    
    # Simulated Portfolio
    my_portfolio = {"NVDA", "AAPL", "MSFT"}
    print(f"\nMy Portfolio: {my_portfolio}")
    
    # Scenario: TSMC (TSM) has manufacturing problems
    bad_news_ticker = "TSM"
    print(f"\n[ALERT] Bad news detected for {bad_news_ticker}!")
    
    risks = graph.check_portfolio_risk_exposure(bad_news_ticker, my_portfolio)
    if risks:
        print("Cascading Risk Detected for your portfolio:")
        for affected_ticker, exposure_type in risks:
            print(f" -> {affected_ticker} is at risk because {bad_news_ticker} is its {exposure_type}.")
    else:
        print("Your portfolio has no direct exposure to this company.")

if __name__ == "__main__":
    run_simulation()
    test_stock_cache()
    test_portfolio_tree()
    test_company_graph()
