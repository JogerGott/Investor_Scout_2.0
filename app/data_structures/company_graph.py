from typing import Dict, List, Set, Tuple

class CompanyRelationshipGraph:
    """
    Graph data structure representing relationships between companies.
    Nodes = Companies (Tickers)
    Edges = Relationships (Supplier, Customer, Competitor)
    
    Used to detect cascading risks (e.g., if a supplier has issues, which portfolio companies are exposed?)
    """
    def __init__(self):
        # Adjacency List: ticker -> List of (Related Ticker, Relationship Type)
        self.adj_list: Dict[str, List[Tuple[str, str]]] = {}

    def add_company(self, ticker: str):
        ticker = ticker.upper()
        if ticker not in self.adj_list:
            self.adj_list[ticker] = []

    def add_relationship(self, ticker1: str, ticker2: str, relationship_type: str):
        """
        Adds a directed relationship from ticker1 to ticker2.
        e.g., ticker1="NVDA", ticker2="TSM", relationship_type="SUPPLIER"
        Means TSM is a SUPPLIER to NVDA.
        """
        ticker1 = ticker1.upper()
        ticker2 = ticker2.upper()
        relationship_type = relationship_type.upper()
        
        self.add_company(ticker1)
        self.add_company(ticker2)
        
        # Avoid duplicate edges
        if not any(rel[0] == ticker2 and rel[1] == relationship_type for rel in self.adj_list[ticker1]):
            self.adj_list[ticker1].append((ticker2, relationship_type))

    def add_bidirectional_relationship(self, ticker1: str, ticker2: str, relationship_type: str):
        """Useful for symmetrical relationships like 'COMPETITOR'."""
        self.add_relationship(ticker1, ticker2, relationship_type)
        self.add_relationship(ticker2, ticker1, relationship_type)

    def get_related_companies(self, ticker: str) -> List[Tuple[str, str]]:
        ticker = ticker.upper()
        return self.adj_list.get(ticker, [])

    def check_portfolio_risk_exposure(self, problematic_ticker: str, portfolio_tickers: Set[str]) -> List[Tuple[str, str]]:
        """
        If `problematic_ticker` is facing issues (e.g., bad earnings, geopolitical risk), 
        which companies in our portfolio are exposed to it, and how?
        
        Returns a list of tuples: (Portfolio Ticker, How it's exposed)
        """
        problematic_ticker = problematic_ticker.upper()
        exposed_companies = []
        
        for p_ticker in portfolio_tickers:
            p_ticker = p_ticker.upper()
            if p_ticker == problematic_ticker:
                continue
                
            # Check the portfolio company's edges to see if it points to the problematic ticker
            for related_ticker, rel_type in self.adj_list.get(p_ticker, []):
                if related_ticker == problematic_ticker:
                    exposed_companies.append((p_ticker, rel_type))
                    
        return exposed_companies

    def display_graph(self):
        """Prints the graph structure for debugging."""
        for ticker, edges in self.adj_list.items():
            if not edges:
                continue
            print(f"[{ticker}]")
            for related, rel_type in edges:
                print(f"  |-- {rel_type} -> {related}")
