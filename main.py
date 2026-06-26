import logging
from datetime import datetime, date
import time
import sys
from typing import Optional, List, Dict, Any, Set

# Configure logging to write to a log file instead of terminal
# to prevent cluttering the CLI menu
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

# Models and In-Memory Data Structures
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.company import Company
from app.data_structures.portfolio_tree import PortfolioRootNode, SectorNode, CompanyNode
from app.data_structures.company_graph import CompanyRelationshipGraph
from app.data_structures.stock_cache import StockCache
from app.data_structures.undo_stack import UndoStack
from app.data_structures.sync_queue import SyncQueue
from app.services.portfolio_service import PortfolioService

# Database and ETL System
from scripts.init_db import initialize_database
from app.database.connection import DBConnectionManager
from app.services.yahoo_provider import YahooFinanceProvider
from app.services.sync_service import SyncService
from app.repositories.activo_repository import ActivoRepository
from app.repositories.ratios_repository import RatiosRepository
from app.repositories.income_repository import IncomeRepository
from app.repositories.balance_repository import BalanceRepository
from app.repositories.cash_flow_repository import CashFlowRepository
from app.repositories.historico_repository import HistoricoRepository
from app.repositories.equity_repository import EquityRepository
from app.repositories.metrics_repository import MetricsRepository

# Database persistence for Users, Portfolios, Transactions and Positions
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.portafolio_repository import PortafolioRepository
from app.repositories.movimiento_repository import MovimientoRepository
from app.repositories.posicion_repository import PosicionRepository

# Global instances
stock_cache = StockCache()
undo_stack = UndoStack()

# =====================================================================
# DATA STRUCTURE UTILITIES
# =====================================================================

def build_portfolio_tree(portfolio: Portfolio) -> PortfolioRootNode:
    """
    Constructs a PortfolioRootNode tree from the current holdings.
    Recursively values the holdings grouped by sector.
    """
    root = PortfolioRootNode(portfolio.name, portfolio.cash_balance)
    sector_nodes = {}
    
    activo_repo = ActivoRepository()
    equity_repo = EquityRepository()
    
    for ticker, holding in portfolio.holdings.items():
        current_price = stock_cache.get_price(ticker) or holding.avg_cost
        
        # Determine sector
        sector_name = "Other"
        asset = activo_repo.get_by_ticker(ticker)
        if asset:
            if asset.tipo_activo == "EQUITY":
                details = equity_repo.get_by_id(asset.id_activo)
                if details and details.sector:
                    sector_name = details.sector
            elif asset.tipo_activo == "BOND":
                sector_name = "Fixed Income"
                
        if sector_name not in sector_nodes:
            sec_node = SectorNode(sector_name)
            root.add_child(sec_node)
            sector_nodes[sector_name] = sec_node
            
        comp_node = CompanyNode(ticker=ticker, shares=holding.shares, current_price=current_price)
        sector_nodes[sector_name].add_child(comp_node)
        
    return root

def init_relationship_graph() -> CompanyRelationshipGraph:
    """
    Initializes a relationship graph engine (Graph data structure).
    """
    graph = CompanyRelationshipGraph()
    graph.add_relationship("NVDA", "TSM", "SUPPLIER")
    graph.add_relationship("AAPL", "TSM", "SUPPLIER")
    graph.add_relationship("MSFT", "NVDA", "CUSTOMER")
    graph.add_bidirectional_relationship("NVDA", "AMD", "COMPETITOR")
    graph.add_relationship("TSLA", "NVDA", "CUSTOMER")
    graph.add_relationship("AMZN", "NVDA", "CUSTOMER")
    graph.add_relationship("GOOGL", "NVDA", "CUSTOMER")
    graph.add_relationship("META", "NVDA", "CUSTOMER")
    return graph

def process_batch_sync_queue(sync_queue: SyncQueue, sync_service: SyncService):
    """
    FIFO Queue processing: Dequeues and synchronizes tickers sequentially.
    """
    if sync_queue.is_empty():
        print("[INFO] La cola de sincronización está vacía.")
        return
        
    print(f"\n[QUEUE] Iniciando sincronización por lotes de {sync_queue.size()} tickers (Procesamiento FIFO)...")
    while not sync_queue.is_empty():
        ticker = sync_queue.dequeue()
        print(f" -> Procesando {ticker}...")
        try:
            success = sync_service.sync_initial(ticker)
            if success:
                print(f"    [ÉXITO] {ticker} sincronizado.")
            else:
                print(f"    [FALLO] No se pudo sincronizar {ticker}.")
        except Exception as e:
            print(f"    [ERROR] Excepción al sincronizar {ticker}: {e}")
    print("[QUEUE] Procesamiento de cola finalizado.")

def get_or_sync_asset(ticker: str) -> Optional[int]:
    """
    Checks if asset exists in DB, otherwise fetches using SyncService.
    """
    activo_repo = ActivoRepository()
    asset = activo_repo.get_by_ticker(ticker)
    if not asset:
        print(f"\n[ETL] Ticker '{ticker}' no encontrado en BD. Sincronizando con Yahoo Finance...")
        provider = YahooFinanceProvider()
        sync_service = SyncService(provider=provider, stock_cache=stock_cache)
        success = sync_service.sync_initial(ticker)
        if not success:
            print(f"[ERROR] No se pudo obtener información de mercado para {ticker}.")
            return None
        asset = activo_repo.get_by_ticker(ticker)
    return asset.id_activo if asset else None

# =====================================================================
# CLI SUBMENU ACTIONS
# =====================================================================

# --- 1. USUARIOS ---

def show_users() -> bool:
    repo = ClienteRepository()
    users = repo.get_all()
    if not users:
        print("\n[INFO] No hay usuarios registrados en el sistema.")
        return False
    print("\n========================================================================")
    print("                      USUARIOS REGISTRADOS")
    print("========================================================================")
    print(f"{'ID':<5} | {'Nombre Completo':<25} | {'Email':<30} | {'Teléfono':<15}")
    print("-" * 83)
    for u in users:
        print(f"{u.user_id:<5} | {f'{u.first_name} {u.last_name}':<25} | {u.email:<30} | {u.telephone or 'N/A':<15}")
    return True

def create_user():
    print("\n========================================================")
    print("                     CREAR CUENTA")
    print("========================================================")
    first_name = input("Nombre: ").strip()
    last_name = input("Apellido: ").strip()
    email = input("Email: ").strip()
    password = input("Contraseña: ").strip()
    telephone = input("Teléfono: ").strip()
    
    if not first_name or not last_name or not email or not password:
        print("\n[ERROR] Todos los campos excepto teléfono son obligatorios.")
        return
        
    repo = ClienteRepository()
    existing = repo.get_by_email(email)
    if existing:
        print(f"\n[ERROR] El correo electrónico '{email}' ya se encuentra registrado.")
        return
        
    user = User(
        user_id=0,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=password, # In real app, hash password using bcrypt
        telephone=telephone if telephone else None
    )
    try:
        user_id = repo.save(user)
        print(f"\n[ÉXITO] Usuario creado exitosamente con ID: {user_id}")
    except Exception as e:
        print(f"\n[ERROR] No se pudo registrar el usuario: {e}")

# --- 2. PORTAFOLIOS ---

def show_portfolios() -> bool:
    repo = PortafolioRepository()
    ports = repo.get_all()
    if not ports:
        print("\n[INFO] No hay portafolios registrados en el sistema.")
        return False
    
    cliente_repo = ClienteRepository()
    print("\n=========================================================================================")
    print("                                PORTAFOLIOS REGISTRADOS")
    print("=========================================================================================")
    print(f"{'ID':<5} | {'Nombre Portafolio':<30} | {'ID Cliente':<10} | {'Propietario':<25} | {'Efectivo (USD)':<15}")
    print("-" * 92)
    for p in ports:
        owner = cliente_repo.get_by_id(p.user_id)
        owner_name = f"{owner.first_name} {owner.last_name}" if owner else "Desconocido"
        print(f"{p.portfolio_id:<5} | {p.name:<30} | {p.user_id:<10} | {owner_name:<25} | ${p.cash_balance:,.2f}")
    return True

def create_portfolio():
    print("\n========================================================")
    print("                     CREAR PORTAFOLIO")
    print("========================================================")
    if not show_users():
        print("[ERROR] Debe crear un usuario primero.")
        return
        
    try:
        user_id = int(input("\nIngrese el ID del usuario propietario: "))
    except ValueError:
        print("[ERROR] ID de usuario debe ser un número entero.")
        return
        
    cliente_repo = ClienteRepository()
    owner = cliente_repo.get_by_id(user_id)
    if not owner:
        print(f"[ERROR] No existe ningún usuario con el ID {user_id}.")
        return
        
    name = input("Nombre del Portafolio: ").strip()
    if not name:
        print("[ERROR] El nombre del portafolio es obligatorio.")
        return
        
    try:
        cash = float(input("Efectivo Inicial en USD: "))
        if cash < 0:
            print("[ERROR] El efectivo no puede ser negativo.")
            return
    except ValueError:
        print("[ERROR] Monto de efectivo inválido.")
        return
        
    portfolio = Portfolio(
        portfolio_id=0,
        user_id=user_id,
        name=name,
        cash_balance=cash
    )
    
    port_repo = PortafolioRepository()
    try:
        port_id = port_repo.save(portfolio)
        print(f"\n[ÉXITO] Portafolio '{name}' registrado con ID: {port_id}")
    except Exception as e:
        print(f"\n[ERROR] No se pudo crear el portafolio: {e}")

# --- 3. TRANSACCIONES ---

def handle_transaction(trans_type: str):
    print("\n========================================================")
    print(f"               REGISTRAR COMPRA/VENTA ({trans_type})")
    print("========================================================")
    if not show_portfolios():
        return
        
    try:
        port_id = int(input("\nIngrese el ID del portafolio: "))
    except ValueError:
        print("[ERROR] ID de portafolio inválido.")
        return
        
    port_repo = PortafolioRepository()
    portfolio = port_repo.get_by_id(port_id)
    if not portfolio:
        print(f"[ERROR] No se encontró el portafolio con ID {port_id}.")
        return
        
    # Chronologically reconstruct from database
    mov_repo = MovimientoRepository()
    portfolio.transaction_log = mov_repo.get_all_by_portafolio(port_id)
    portfolio._recalculate_holdings()
    
    ticker = input("Ticker del Activo (ej. AAPL, NVDA): ").strip().upper()
    if not ticker:
        print("[ERROR] Ticker no puede estar vacío.")
        return
        
    try:
        shares = float(input("Cantidad de Acciones (Shares): "))
        price = float(input("Precio por Acción (USD): "))
        if shares <= 0 or price <= 0:
            print("[ERROR] Cantidad y precio deben ser mayores a cero.")
            return
    except ValueError:
        print("[ERROR] Cantidad o precio inválidos.")
        return
        
    # Get or sync asset first to get asset ID
    id_activo = get_or_sync_asset(ticker)
    if not id_activo:
        return
        
    try:
        # Run transaction in Python model (checks funds / short selling)
        portfolio.add_transaction(ticker, trans_type, shares, price, datetime.now())
        
        # Save movement transaction log to DB
        id_mov = mov_repo.save(
            id_portafolio=port_id,
            id_activo=id_activo,
            tipo_mov=trans_type,
            cantidad=shares,
            precio_por_accion=price,
            date=datetime.now()
        )
        
        # Update portfolio cash balance in DB
        port_repo.update_cash(port_id, portfolio.cash_balance)
        
        # Update active holdings positions in DB
        posicion_repo = PosicionRepository()
        activo_repo = ActivoRepository()
        
        for t_ticker, holding in portfolio.holdings.items():
            t_asset = activo_repo.get_by_ticker(t_ticker)
            c_price = stock_cache.get_price(t_ticker) or holding.avg_cost
            holding.update_value(c_price)
            unrealized = (c_price - holding.avg_cost) * holding.shares
            posicion_repo.save(
                id_portafolio=port_id,
                id_activo=t_asset.id_activo,
                shares=holding.shares,
                avg_cost=holding.avg_cost,
                market_value=holding.current_value,
                unrealized_pnl=unrealized
            )
            
        # Delete positions that are now empty (shares = 0)
        db_positions = posicion_repo.get_all_by_portafolio(port_id)
        for db_pos in db_positions:
            if db_pos.ticker not in portfolio.holdings:
                posicion_repo.delete(port_id, db_pos.id_activo)
                
        # Push operation to session undo stack
        undo_stack.push({
            "portfolio_id": port_id,
            "id_movimiento": id_mov,
            "ticker": ticker,
            "type": trans_type,
            "shares": shares,
            "price": price
        })
        
        print(f"\n[ÉXITO] Transacción registrada.")
        print(f"Efectivo restante en Portafolio: ${portfolio.cash_balance:,.2f}")
        if ticker in portfolio.holdings:
            print(f"Holding actualizado: {ticker} | Shares: {portfolio.holdings[ticker].shares:.4f} | Costo Promedio: ${portfolio.holdings[ticker].avg_cost:.2f}")
        else:
            print(f"Holding de {ticker} ahora está completamente liquidado.")
            
    except ValueError as ve:
        print(f"\n[ERROR DE REGLA DE NEGOCIO] {ve}")
    except Exception as e:
        print(f"\n[ERROR] No se pudo ejecutar la transacción: {e}")

def handle_undo():
    print("\n========================================================")
    print("                 DESHACER ÚLTIMA OPERACIÓN")
    print("========================================================")
    if undo_stack.is_empty():
        print("[INFO] No hay transacciones ejecutadas en esta sesión para revertir.")
        return
        
    tx_info = undo_stack.peek()
    port_id = tx_info["portfolio_id"]
    port_repo = PortafolioRepository()
    portfolio = port_repo.get_by_id(port_id)
    if not portfolio:
        print("[ERROR] Portafolio no encontrado.")
        undo_stack.clear()
        return
        
    confirm = input(f"¿Desea revertir la última operación ({tx_info['type']} {tx_info['shares']} {tx_info['ticker']} @ ${tx_info['price']})? (s/n): ").strip().lower()
    if confirm != 's':
        print("Operación cancelada.")
        return
        
    tx_info = undo_stack.pop()
    id_port = tx_info["portfolio_id"]
    id_mov = tx_info["id_movimiento"]
    
    mov_repo = MovimientoRepository()
    posicion_repo = PosicionRepository()
    activo_repo = ActivoRepository()
    
    try:
        # Safety check: Verify DB latest movement matches this ID
        conn = DBConnectionManager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_movimiento, tipo_mov, cantidad, precio_por_accion FROM movimiento WHERE id_portafolio = %s ORDER BY fecha_transaccion DESC, id_movimiento DESC LIMIT 1", (id_port,))
        res = cursor.fetchone()
        if not res or res[0] != id_mov:
            print("[ERROR] Error de sincronización. La última transacción de la BD no coincide con la sesión. No se puede revertir.")
            cursor.close()
            conn.close()
            return
        cursor.close()
        conn.close()
        
        # Delete latest transaction
        mov_repo.delete_latest(id_port)
        
        # Reverse cash change
        shares = tx_info["shares"]
        price = tx_info["price"]
        if tx_info["type"] == "BUY":
            portfolio.cash_balance += shares * price
        else:
            portfolio.cash_balance -= shares * price
            
        # Rebuild holdings from remaining logs
        portfolio.transaction_log = mov_repo.get_all_by_portafolio(id_port)
        portfolio._recalculate_holdings()
        
        # Save cash back to DB
        port_repo.update_cash(id_port, portfolio.cash_balance)
        
        # Save updated positions to DB
        for t_ticker, holding in portfolio.holdings.items():
            t_asset = activo_repo.get_by_ticker(t_ticker)
            c_price = stock_cache.get_price(t_ticker) or holding.avg_cost
            holding.update_value(c_price)
            unrealized = (c_price - holding.avg_cost) * holding.shares
            posicion_repo.save(
                id_portafolio=id_port,
                id_activo=t_asset.id_activo,
                shares=holding.shares,
                avg_cost=holding.avg_cost,
                market_value=holding.current_value,
                unrealized_pnl=unrealized
            )
            
        # Delete positions that are no longer active
        db_positions = posicion_repo.get_all_by_portafolio(id_port)
        for db_pos in db_positions:
            if db_pos.ticker not in portfolio.holdings:
                posicion_repo.delete(id_port, db_pos.id_activo)
                
        print("\n[ÉXITO] Transacción eliminada de la base de datos.")
        print(f"Efectivo restaurado: ${portfolio.cash_balance:,.2f}")
    except Exception as e:
        print(f"\n[ERROR] No se pudo deshacer la transacción: {e}")

def show_portfolio_movements():
    print("\n========================================================")
    print("             HISTORIAL DE MOVIMIENTOS (LINKED LIST)")
    print("========================================================")
    if not show_portfolios():
        return
        
    try:
        port_id = int(input("\nIngrese el ID del portafolio: "))
    except ValueError:
        print("[ERROR] ID inválido.")
        return
        
    mov_repo = MovimientoRepository()
    ll = mov_repo.get_all_by_portafolio(port_id)
    
    # Traverse through the TransactionLinkedList (O(N) search/display)
    nodes = list(ll)
    if not nodes:
        print("\n[INFO] No hay transacciones registradas en este portafolio.")
        return
        
    print(f"\nHistorial de movimientos para el Portafolio ID {port_id}:")
    print(f"{'ID Mov':<8} | {'Fecha Transacción':<20} | {'Ticker':<10} | {'Tipo':<6} | {'Acciones':<12} | {'Precio (USD)':<12} | {'Total (USD)':<12}")
    print("-" * 92)
    for node in nodes:
        total = node.shares * node.price
        date_str = node.date.strftime("%Y-%m-%d %H:%M:%S") if isinstance(node.date, datetime) else str(node.date)
        id_mov = getattr(node, "id_movimiento", "N/A")
        print(f"{id_mov:<8} | {date_str:<20} | {node.ticker:<10} | {node.transaction_type:<6} | {node.shares:<12.4f} | ${node.price:<11.2f} | ${total:<11.2f}")

# --- 4. MERCADO ---

def show_company_info():
    ticker = input("\nIngrese Ticker de la Empresa (ej. AAPL): ").strip().upper()
    if not ticker:
        return
    id_activo = get_or_sync_asset(ticker)
    if not id_activo:
        return
        
    activo_repo = ActivoRepository()
    equity_repo = EquityRepository()
    asset = activo_repo.get_by_ticker(ticker)
    details = equity_repo.get_by_id(id_activo) if asset.tipo_activo == "EQUITY" else None
    
    print("\n========================================================")
    print(f"             INFORMACIÓN DE LA EMPRESA: {ticker}")
    print("========================================================")
    print(f"Nombre Oficial:     {asset.nombre}")
    print(f"Tipo de Activo:     {asset.tipo_activo}")
    print(f"Moneda Base:        {asset.moneda}")
    print(f"Bolsa (Exchange):   {asset.exchange or 'N/A'}")
    print(f"País de Origen:     {asset.pais or 'N/A'}")
    if details:
        print(f"Sector Económico:   {details.sector or 'N/A'}")
        print(f"Industria:          {details.industria or 'N/A'}")
        print(f"Fecha Resultados:   {details.earnings_date or 'N/A'}")

def show_market_metrics():
    ticker = input("\nIngrese Ticker de la Empresa (ej. AAPL): ").strip().upper()
    if not ticker:
        return
    id_activo = get_or_sync_asset(ticker)
    if not id_activo:
        return
        
    metrics_repo = MetricsRepository()
    metrics = metrics_repo.get_latest(id_activo)
    if not metrics:
        print("[INFO] No hay métricas registradas en la base de datos.")
        return
        
    print("\n========================================================")
    print(f"           MÉTRICAS DE MERCADO DE {ticker}")
    print("========================================================")
    print(f"Fecha Cálculo:      {metrics.fecha}")
    print(f"Precio de Mercado:  ${metrics.precio:,.2f}" if metrics.precio else "Precio: N/A")
    print(f"Market Cap:         ${metrics.market_cap:,.2f}" if metrics.market_cap else "Market Cap: N/A")
    print(f"Enterprise Value:   ${metrics.enterprise_value:,.2f}" if metrics.enterprise_value else "EV: N/A")
    print(f"P/E Ratio:          {metrics.pe_ratio:.2f}" if metrics.pe_ratio else "P/E: N/A")
    print(f"P/E Forward:        {metrics.pe_forward:.2f}" if metrics.pe_forward else "P/E Forward: N/A")
    print(f"P/B Ratio:          {metrics.pb_ratio:.2f}" if metrics.pb_ratio else "P/B: N/A")
    print(f"P/S Ratio:          {metrics.ps_ratio:.2f}" if metrics.ps_ratio else "P/S: N/A")
    print(f"PEG Ratio:          {metrics.peg:.2f}" if metrics.peg else "PEG: N/A")
    print(f"Beta:               {metrics.beta:.2f}" if metrics.beta else "Beta: N/A")
    print(f"Dividend Yield:     {metrics.dividend_yield * 100:.2f}%" if metrics.dividend_yield else "Dividend Yield: N/A")

def show_financial_ratios():
    ticker = input("\nIngrese Ticker de la Empresa (ej. AAPL): ").strip().upper()
    if not ticker:
        return
    id_activo = get_or_sync_asset(ticker)
    if not id_activo:
        return
        
    ratios_repo = RatiosRepository()
    ratios = ratios_repo.get_all(id_activo)
    if not ratios:
        print("[INFO] No hay ratios calculados en la base de datos.")
        return
        
    print("\n=========================================================================================")
    print(f"                            RATIOS FINANCIEROS HISTÓRICOS: {ticker}")
    print("=========================================================================================")
    print(f"{'Periodo':<10} | {'Fecha Reporte':<12} | {'ROE %':<8} | {'ROA %':<8} | {'ROIC %':<8} | {'D/E':<6} | {'Margin Neto %':<15} | {'YoY Rev %':<10} | {'FCF Yield %':<10}")
    print("-" * 102)
    for r in ratios:
        roe_s = f"{r.roe * 100:.2f}%" if r.roe is not None else "N/A"
        roa_s = f"{r.roa * 100:.2f}%" if r.roa is not None else "N/A"
        roic_s = f"{r.roic * 100:.2f}%" if r.roic is not None else "N/A"
        de_s = f"{r.debt_equity:.2f}" if r.debt_equity is not None else "N/A"
        net_m = f"{r.net_margin * 100:.2f}%" if r.net_margin is not None else "N/A"
        rev_g = f"{r.revenue_growth * 100:.2f}%" if r.revenue_growth is not None else "N/A"
        fcf_y = f"{r.fcf_yield * 100:.2f}%" if r.fcf_yield is not None else "N/A"
        
        date_str = r.fecha_reporte.strftime("%Y-%m-%d") if hasattr(r.fecha_reporte, "strftime") else str(r.fecha_reporte)
        print(f"{r.periodo:<10} | {date_str:<12} | {roe_s:<8} | {roa_s:<8} | {roic_s:<8} | {de_s:<6} | {net_m:<15} | {rev_g:<10} | {fcf_y:<10}")

def show_price_history():
    ticker = input("\nIngrese Ticker de la Empresa (ej. AAPL): ").strip().upper()
    if not ticker:
        return
    id_activo = get_or_sync_asset(ticker)
    if not id_activo:
        return
        
    hist_repo = HistoricoRepository()
    prices = hist_repo.get_prices(id_activo)
    if not prices:
        print("[INFO] No hay historial de precios guardados en base de datos.")
        return
        
    print("\n=========================================================================================")
    print(f"                         HISTÓRICO DE PRECIOS EN BD: {ticker} (Últimos 15 días)")
    print("=========================================================================================")
    print(f"{'Fecha':<12} | {'Apertura (USD)':<15} | {'Máximo (USD)':<15} | {'Mínimo (USD)':<15} | {'Cierre (USD)':<15} | {'Volumen':<15}")
    print("-" * 92)
    # Get last 15 prices
    for p in prices[-15:]:
        date_str = p.fecha.strftime("%Y-%m-%d") if hasattr(p.fecha, "strftime") else str(p.fecha)
        o = f"${p.open_price:,.2f}" if p.open_price else "N/A"
        h = f"${p.high_price:,.2f}" if p.high_price else "N/A"
        l = f"${p.low_price:,.2f}" if p.low_price else "N/A"
        c = f"${p.close_price:,.2f}"
        vol = f"{p.volumen:,}" if p.volumen else "N/A"
        print(f"{date_str:<12} | {o:<15} | {h:<15} | {l:<15} | {c:<15} | {vol:<15}")

def handle_cascading_risk_assessment():
    print("\n========================================================")
    print("         EVALUADOR DE RIESGOS DE CASCADA (GRAFOS)")
    print("========================================================")
    if not show_portfolios():
        return
        
    try:
        port_id = int(input("\nIngrese el ID del portafolio a evaluar: "))
    except ValueError:
        print("[ERROR] ID inválido.")
        return
        
    port_repo = PortafolioRepository()
    portfolio = port_repo.get_by_id(port_id)
    if not portfolio:
        print("[ERROR] Portafolio no encontrado.")
        return
        
    # Reconstruct portfolio state
    mov_repo = MovimientoRepository()
    portfolio.transaction_log = mov_repo.get_all_by_portafolio(port_id)
    portfolio._recalculate_holdings()
    
    if not portfolio.holdings:
        print("[INFO] El portafolio no posee posiciones activas.")
        return
        
    portfolio_tickers = set(portfolio.holdings.keys())
    print(f"Posiciones activas del portafolio: {portfolio_tickers}")
    
    graph = init_relationship_graph()
    
    print("\n--- Estructura del Grafo de Dependencias Comerciales ---")
    graph.display_graph()
    
    problematic_ticker = input("\nIngrese la empresa afectada por eventos adversos (ej. TSM, NVDA): ").strip().upper()
    if not problematic_ticker:
        return
        
    risks = graph.check_portfolio_risk_exposure(problematic_ticker, portfolio_tickers)
    if risks:
        print(f"\n[ALERTA DE RIESGO] Exposición crítica en su portafolio:")
        for affected_ticker, exposure_type in risks:
            print(f" -> '{affected_ticker}' está expuesta porque '{problematic_ticker}' es su {exposure_type}.")
    else:
        print(f"\n[INFO] No se detectó exposición al riesgo de '{problematic_ticker}' en el grafo actual.")

def handle_sync_queue():
    print("\n========================================================")
    print("         COLA DE SINCRONIZACIÓN DE TICKERS (COLAS)")
    print("========================================================")
    queue = SyncQueue()
    
    while True:
        print(f"\nCola de Tickers actualmente ({queue.size()}): {queue.get_all()}")
        print("1. Encolar ticker para sincronizar")
        print("2. Procesar cola de sincronización (FIFO)")
        print("3. Limpiar cola")
        print("4. Volver al menú anterior")
        
        choice = input("\nSeleccione una opción: ").strip()
        if choice == '1':
            ticker = input("Ingrese Ticker: ").strip().upper()
            if ticker:
                queue.enqueue(ticker)
                print(f"Ticker {ticker} añadido a la cola FIFO.")
        elif choice == '2':
            if queue.is_empty():
                print("[INFO] La cola está vacía.")
            else:
                provider = YahooFinanceProvider()
                sync_service = SyncService(provider=provider, stock_cache=stock_cache)
                process_batch_sync_queue(queue, sync_service)
        elif choice == '3':
            queue.clear()
            print("Cola vaciada.")
        elif choice == '4':
            break
        else:
            print("[ERROR] Opción no válida.")

# --- 5. ESTADOS FINANCIEROS ---

def show_income_statement():
    ticker = input("\nIngrese Ticker de la Empresa (ej. AAPL): ").strip().upper()
    if not ticker:
        return
    id_activo = get_or_sync_asset(ticker)
    if not id_activo:
        return
        
    inc_repo = IncomeRepository()
    stmts = inc_repo.get_all(id_activo)
    if not stmts:
        print("[INFO] No hay estados de resultados registrados.")
        return
        
    print("\n=========================================================================================")
    print(f"                             ESTADO DE RESULTADOS: {ticker}")
    print("=========================================================================================")
    print(f"{'Periodo':<10} | {'Fecha Reporte':<12} | {'Ingresos Totales':<18} | {'Margen Bruto':<12} | {'Operating Income':<18} | {'Net Income':<18}")
    print("-" * 99)
    for s in stmts:
        margin_bruto = f"{(s.gross_profit / s.revenue * 100):.2f}%" if s.gross_profit and s.revenue else "N/A"
        date_str = s.fecha_reporte.strftime("%Y-%m-%d") if hasattr(s.fecha_reporte, "strftime") else str(s.fecha_reporte)
        rev = f"${s.revenue:,.2f}" if s.revenue is not None else "N/A"
        op_inc = f"${s.operating_income:,.2f}" if s.operating_income is not None else "N/A"
        net_inc = f"${s.net_income:,.2f}" if s.net_income is not None else "N/A"
        print(f"{s.periodo:<10} | {date_str:<12} | {rev:<18} | {margin_bruto:<12} | {op_inc:<18} | {net_inc:<18}")

def show_balance_sheet():
    ticker = input("\nIngrese Ticker de la Empresa (ej. AAPL): ").strip().upper()
    if not ticker:
        return
    id_activo = get_or_sync_asset(ticker)
    if not id_activo:
        return
        
    bal_repo = BalanceRepository()
    balances = bal_repo.get_all(id_activo)
    if not balances:
        print("[INFO] No hay balances generales registrados.")
        return
        
    print("\n=========================================================================================")
    print(f"                                BALANCE GENERAL: {ticker}")
    print("=========================================================================================")
    print(f"{'Periodo':<10} | {'Fecha Reporte':<12} | {'Activos Totales':<18} | {'Pasivos Totales':<18} | {'Patrimonio Neto':<18} | {'Deuda Total':<18}")
    print("-" * 102)
    for b in balances:
        date_str = b.fecha_reporte.strftime("%Y-%m-%d") if hasattr(b.fecha_reporte, "strftime") else str(b.fecha_reporte)
        assets = f"${b.total_assets:,.2f}" if b.total_assets is not None else "N/A"
        liab = f"${b.total_liabilities:,.2f}" if b.total_liabilities is not None else "N/A"
        eq = f"${b.total_equity:,.2f}" if b.total_equity is not None else "N/A"
        debt = f"${b.total_debt:,.2f}" if b.total_debt is not None else "N/A"
        print(f"{b.periodo:<10} | {date_str:<12} | {assets:<18} | {liab:<18} | {eq:<18} | {debt:<18}")

def show_cash_flow():
    ticker = input("\nIngrese Ticker de la Empresa (ej. AAPL): ").strip().upper()
    if not ticker:
        return
    id_activo = get_or_sync_asset(ticker)
    if not id_activo:
        return
        
    cf_repo = CashFlowRepository()
    flows = cf_repo.get_all(id_activo)
    if not flows:
        print("[INFO] No hay flujos de caja registrados.")
        return
        
    print("\n=========================================================================================")
    print(f"                                   FLUJO DE CAJA: {ticker}")
    print("=========================================================================================")
    print(f"{'Periodo':<10} | {'Fecha Reporte':<12} | {'Flujo Operativo':<18} | {'Capex':<18} | {'Free Cash Flow (FCF)':<20}")
    print("-" * 88)
    for cf in flows:
        date_str = cf.fecha_reporte.strftime("%Y-%m-%d") if hasattr(cf.fecha_reporte, "strftime") else str(cf.fecha_reporte)
        op = f"${cf.operating_cf:,.2f}" if cf.operating_cf is not None else "N/A"
        cap = f"${cf.capex:,.2f}" if cf.capex is not None else "N/A"
        fcf = f"${cf.free_cash_flow:,.2f}" if cf.free_cash_flow is not None else "N/A"
        print(f"{cf.periodo:<10} | {date_str:<12} | {op:<18} | {cap:<18} | {fcf:<20}")

# --- 6. CONSULTA DEL PORTAFOLIO ---

def show_portfolio_positions():
    print("\n=========================================================")
    print("                POSICIÓN ACTUAL DEL PORTAFOLIO")
    print("=========================================================")
    if not show_portfolios():
        return
        
    try:
        port_id = int(input("\nIngrese el ID del portafolio: "))
    except ValueError:
        print("[ERROR] ID inválido.")
        return
        
    port_repo = PortafolioRepository()
    portfolio = port_repo.get_by_id(port_id)
    if not portfolio:
        print("[ERROR] Portafolio no encontrado.")
        return
        
    # Reconstruct portfolio holdings
    mov_repo = MovimientoRepository()
    portfolio.transaction_log = mov_repo.get_all_by_portafolio(port_id)
    portfolio._recalculate_holdings()
    
    if not portfolio.holdings:
        print(f"\n[INFO] El portafolio '{portfolio.name}' no tiene posiciones activas.")
        print(f"Efectivo disponible: ${portfolio.cash_balance:,.2f}")
        return
        
    # Recalculate portfolio value based on StockCache (Hash Table)
    total_market_val = 0.0
    for ticker, holding in portfolio.holdings.items():
        price = stock_cache.get_price(ticker) or holding.avg_cost
        holding.update_value(price)
        total_market_val += holding.current_value
        
    total_val = portfolio.cash_balance + total_market_val
    
    print(f"\nPortafolio: '{portfolio.name}'")
    print(f"Efectivo en Caja: ${portfolio.cash_balance:,.2f} | Valor total: ${total_val:,.2f}")
    print("-" * 115)
    print(f"{'Ticker':<10} | {'Acciones':<12} | {'Costo Prom':<12} | {'Precio Act':<12} | {'Valor Merc':<15} | {'P&L No Realiz':<15} | {'Peso %':<8}")
    print("-" * 115)
    for ticker, holding in portfolio.holdings.items():
        price = stock_cache.get_price(ticker) or holding.avg_cost
        mkt_val = holding.current_value
        pnl = (price - holding.avg_cost) * holding.shares
        weight = (mkt_val / total_val * 100) if total_val > 0 else 0.0
        print(f"{ticker:<10} | {holding.shares:<12.4f} | ${holding.avg_cost:<11.2f} | ${price:<11.2f} | ${mkt_val:<14.2f} | ${pnl:<14.2f} | {weight:.2f}%")

def show_portfolio_metrics_cli():
    print("\n=========================================================")
    print("                   MÉTRICAS DEL PORTAFOLIO")
    print("=========================================================")
    if not show_portfolios():
        return
        
    try:
        port_id = int(input("\nIngrese el ID del portafolio: "))
    except ValueError:
        print("[ERROR] ID inválido.")
        return
        
    port_repo = PortafolioRepository()
    portfolio = port_repo.get_by_id(port_id)
    if not portfolio:
        print("[ERROR] Portafolio no encontrado.")
        return
        
    # Replay movements
    mov_repo = MovimientoRepository()
    portfolio.transaction_log = mov_repo.get_all_by_portafolio(port_id)
    portfolio._recalculate_holdings()
    
    # Calculate metrics using PortfolioService
    service = PortfolioService(stock_cache=stock_cache)
    metrics = service.get_portfolio_metrics(portfolio)
    
    # Invested Capital & Returns
    capital_invested = sum(h.avg_cost * h.shares for h in portfolio.holdings.values())
    unrealized_pnl = metrics["Unrealized P&L"]
    realized_pnl = metrics["Realized P&L"]
    total_pnl = unrealized_pnl + realized_pnl
    return_pct = (total_pnl / capital_invested * 100) if capital_invested > 0 else 0.0
    num_positions = len(portfolio.holdings)
    
    print(f"\nPortafolio: '{portfolio.name}'")
    print(f"Valor Total de Mercado:  ${metrics['Total Value']:,.2f}")
    print(f"Efectivo Disponible:     ${metrics['Cash Balance']:,.2f}")
    print(f"Capital Invertido:       ${capital_invested:,.2f}")
    print(f"Rentabilidad Total:      {return_pct:.2f}% (${total_pnl:,.2f})")
    print(f"Ganancia/Pérdida Realiz:  ${realized_pnl:,.2f}")
    print(f"Ganancia/Pérdida No Real:${unrealized_pnl:,.2f}")
    print(f"Número de Posiciones:    {num_positions}")
    
    print("\nDistribución por Activo:")
    for ticker, pct in metrics["Allocations (%)"].items():
        print(f"  * {ticker}: {pct}%")

def show_portfolio_valuation_tree():
    print("\n=========================================================")
    print("              ÁRBOL DE VALUACIÓN DEL PORTAFOLIO")
    print("=========================================================")
    if not show_portfolios():
        return
        
    try:
        port_id = int(input("\nIngrese el ID del portafolio: "))
    except ValueError:
        print("[ERROR] ID inválido.")
        return
        
    port_repo = PortafolioRepository()
    portfolio = port_repo.get_by_id(port_id)
    if not portfolio:
        print("[ERROR] Portafolio no encontrado.")
        return
        
    # Replay movements
    mov_repo = MovimientoRepository()
    portfolio.transaction_log = mov_repo.get_all_by_portafolio(port_id)
    portfolio._recalculate_holdings()
    
    # Build tree
    print(f"\nEstructura arbórea de valuación (Recursive Tree display):")
    root = build_portfolio_tree(portfolio)
    root.display()
    print(f"Valor total calculado recursivamente: ${root.get_value():,.2f}")

# =====================================================================
# DEMO FUNCTIONS (MAINTAINING ORIGINAL Demos)
# =====================================================================

def run_database_etl_demo():
    print("\n==================================================")
    print("      INVESTOR SCOUT: DATABASE ETL SYNC DEMO      ")
    print("==================================================")
    
    db_ok = initialize_database()
    if not db_ok:
        print("Database initialization failed. Cannot run MySQL ETL demo.")
        return False
        
    provider = YahooFinanceProvider()
    cache = StockCache()
    sync_service = SyncService(provider=provider, stock_cache=cache)
    
    ticker = "AAPL"
    
    print(f"\n[ETL STAGE 1] Running INITIAL sync for {ticker} (historical prices + financial statements)...")
    success = sync_service.sync_initial(ticker)
    if not success:
        print(f"Failed initial sync for {ticker}")
        return False
        
    print(f"\n[ETL STAGE 2] Running DAILY sync for {ticker} (price + market metrics update)...")
    sync_service.sync_daily(ticker)
    
    print(f"\n[ETL STAGE 3] Querying MySQL tables to verify stored statements & computed ratios...")
    activo_repo = ActivoRepository()
    asset = activo_repo.get_by_ticker(ticker)
    if asset:
        print(f" -> Found Asset in MySQL Table 'activo': {asset.nombre} ({asset.ticker})")
        print(f"    Exchange: {asset.exchange} | Country: {asset.pais} | Currency: {asset.moneda}")
        
        income_repo = IncomeRepository()
        statements = income_repo.get_all(asset.id_activo)
        print(f" -> Stored Income Statements count: {len(statements)}")
        if statements:
            latest = statements[0]
            print(f"    Latest Statement Period: {latest.periodo} | Date: {latest.fecha_reporte}")
            revenue_str = f"${latest.revenue:,.2f}" if latest.revenue is not None else "N/A"
            net_inc_str = f"${latest.net_income:,.2f}" if latest.net_income is not None else "N/A"
            print(f"    Revenue: {revenue_str} | Net Income: {net_inc_str}")
            
        ratios_repo = RatiosRepository()
        ratios_list = ratios_repo.get_all(asset.id_activo)
        print(f" -> Stored Calculated Financial Ratios count: {len(ratios_list)}")
        for r in ratios_list[:2]:
            print(f"    Period: {r.periodo} | Date: {r.fecha_reporte}")
            print(f"      ROIC: {f'{r.roic*100:.2f}%' if r.roic else 'N/A'}")
            print(f"      Gross Margin: {f'{r.gross_margin*100:.2f}%' if r.gross_margin else 'N/A'} | Net Margin: {f'{r.net_margin*100:.2f}%' if r.net_margin else 'N/A'}")
            
    print(f"\n[ETL STAGE 4] Verifying in-memory StockCache sync...")
    price = cache.get_price(ticker)
    if price:
        print(f" -> Retrieved {ticker} from StockCache (O(1) memory): ${price:.2f}")
        
    return True

def run_portfolio_simulation():
    print("\n==================================================")
    print("        IN-MEMORY PORTFOLIO & TREE STRUCTURE      ")
    print("==================================================")
    
    user = User(
        user_id=1, 
        first_name="Joger", 
        last_name="Munoz", 
        email="joger@investorscout.com", 
        password_hash="***", 
    )
    print(f"User created: {user.first_name} {user.last_name}")

    portfolio = Portfolio(
        portfolio_id=1,
        user_id=user.user_id,
        name="Value Investing Portfolio",
        cash_balance=10000.0
    )
    user.portfolios.append(portfolio)
    print(f"Portfolio initialized: '{portfolio.name}' with Cash: ${portfolio.cash_balance:.2f}")

    print("\nExecuting Transactions...")
    portfolio.add_transaction(ticker="AAPL", trans_type="BUY", shares=10, price=150.0, date=datetime.now())
    print(f" -> BUY 10 AAPL @ $150.0")
    portfolio.add_transaction(ticker="NVDA", trans_type="BUY", shares=5, price=400.0, date=datetime.now())
    print(f" -> BUY 5 NVDA @ $400.0")
    portfolio.add_transaction(ticker="AAPL", trans_type="SELL", shares=5, price=180.0, date=datetime.now())
    print(f" -> SELL 5 AAPL @ $180.0")
    
    print("\n--- Current Holdings ---")
    for ticker, holding in portfolio.holdings.items():
        print(f"Holding: {holding.ticker} | Shares: {holding.shares} | Avg Cost Basis: ${holding.avg_cost:.2f}")
    print(f"Remaining Cash Balance: ${portfolio.cash_balance:.2f}")
    
    print("\n--- Testing PortfolioTree (Recursive Valuation) ---")
    root = PortfolioRootNode(name="My Value Portfolio", cash_balance=portfolio.cash_balance)
    tech_sector = SectorNode("Technology")
    root.add_child(tech_sector)
    
    cache = StockCache()
    cache.set_price("AAPL", 250.0)
    cache.set_price("NVDA", 450.0)
    
    for ticker, holding in portfolio.holdings.items():
        price = cache.get_price(ticker) or holding.avg_cost
        node = CompanyNode(ticker=ticker, shares=holding.shares, current_price=price)
        tech_sector.add_child(node)
        
    root.display()
    print(f"Total Portfolio Recursive Value: ${root.get_value():.2f}")

def run_relationship_graph_demo():
    print("\n==================================================")
    print("      COMPANY RELATIONSHIP GRAPH (RISK ENGINE)    ")
    print("==================================================")
    graph = CompanyRelationshipGraph()
    graph.add_relationship("NVDA", "TSM", "SUPPLIER")
    graph.add_relationship("AAPL", "TSM", "SUPPLIER")
    graph.add_relationship("MSFT", "NVDA", "CUSTOMER")
    graph.add_bidirectional_relationship("NVDA", "AMD", "COMPETITOR")
    
    print("Graph Structure:")
    graph.display_graph()
    
    my_portfolio = {"NVDA", "AAPL", "MSFT"}
    bad_news_ticker = "TSM"
    print(f"\n[ALERT] Bad news detected for {bad_news_ticker}!")
    
    risks = graph.check_portfolio_risk_exposure(bad_news_ticker, my_portfolio)
    if risks:
        print("Cascading Risk Detected for your portfolio:")
        for affected_ticker, exposure_type in risks:
            print(f" -> {affected_ticker} is at risk because {bad_news_ticker} is its {exposure_type}.")
    else:
        print("Your portfolio has no exposure to this company.")

# =====================================================================
# MAIN CLI MENU SYSTEM
# =====================================================================

def main_menu():
    # Make sure DB and tables are initialized
    initialize_database()
    
    while True:
        print("\n========================================")
        print("            INVESTOR SCOUT")
        print("========================================")
        print("1. Usuarios")
        print("2. Portafolios")
        print("3. Transacciones")
        print("4. Mercado")
        print("5. Estados Financieros")
        print("6. Portafolio")
        print("7. Histórico")
        print("8. Salir")
        print("========================================")
        
        choice = input("Seleccione una categoría: ").strip()
        
        if choice == '1':
            while True:
                print("\n--- CATEGORÍA: USUARIOS ---")
                print("1. Crear una cuenta")
                print("2. Mostrar usuarios registrados")
                print("3. Volver al menú principal")
                opt = input("Seleccione una opción: ").strip()
                if opt == '1':
                    create_user()
                elif opt == '2':
                    show_users()
                elif opt == '3':
                    break
                else:
                    print("[ERROR] Opción no válida.")
                    
        elif choice == '2':
            while True:
                print("\n--- CATEGORÍA: PORTAFOLIOS ---")
                print("1. Crear portafolio para un usuario")
                print("2. Mostrar portafolios registrados")
                print("3. Volver al menú principal")
                opt = input("Seleccione una opción: ").strip()
                if opt == '1':
                    create_portfolio()
                elif opt == '2':
                    show_portfolios()
                elif opt == '3':
                    break
                else:
                    print("[ERROR] Opción no válida.")
                    
        elif choice == '3':
            while True:
                print("\n--- CATEGORÍA: TRANSACCIONES ---")
                print("1. Registrar compra (BUY)")
                print("2. Registrar segunda compra (BUY) de un activo")
                print("3. Registrar venta (SELL)")
                print("4. Mostrar historial de movimientos (LinkedList)")
                print("5. Deshacer última transacción (LIFO Stack)")
                print("6. Volver al menú principal")
                opt = input("Seleccione una opción: ").strip()
                if opt == '1' or opt == '2':
                    handle_transaction("BUY")
                elif opt == '3':
                    handle_transaction("SELL")
                elif opt == '4':
                    show_portfolio_movements()
                elif opt == '5':
                    handle_undo()
                elif opt == '6':
                    break
                else:
                    print("[ERROR] Opción no válida.")
                    
        elif choice == '4':
            while True:
                print("\n--- CATEGORÍA: MERCADO ---")
                print("1. Información general de la empresa")
                print("2. Métricas de mercado")
                print("3. Ratios financieros")
                print("4. Histórico de precios de mercado")
                print("5. Evaluador de riesgos en cascada (Grafos)")
                print("6. Cola de sincronización de Tickers (Colas FIFO)")
                print("7. Volver al menú principal")
                opt = input("Seleccione una opción: ").strip()
                if opt == '1':
                    show_company_info()
                elif opt == '2':
                    show_market_metrics()
                elif opt == '3':
                    show_financial_ratios()
                elif opt == '4':
                    show_price_history()
                elif opt == '5':
                    handle_cascading_risk_assessment()
                elif opt == '6':
                    handle_sync_queue()
                elif opt == '7':
                    break
                else:
                    print("[ERROR] Opción no válida.")
                    
        elif choice == '5':
            while True:
                print("\n--- CATEGORÍA: ESTADOS FINANCIEROS ---")
                print("1. Estado de resultados")
                print("2. Balance general")
                print("3. Flujo de caja")
                print("4. Volver al menú principal")
                opt = input("Seleccione una opción: ").strip()
                if opt == '1':
                    show_income_statement()
                elif opt == '2':
                    show_balance_sheet()
                elif opt == '3':
                    show_cash_flow()
                elif opt == '4':
                    break
                else:
                    print("[ERROR] Opción no válida.")
                    
        elif choice == '6':
            while True:
                print("\n--- CATEGORÍA: PORTAFOLIO ---")
                print("1. Mostrar posición actual")
                print("2. Mostrar métricas del portafolio")
                print("3. Mostrar árbol de valuación (Estructura de Árbol)")
                print("4. Volver al menú principal")
                opt = input("Seleccione una opción: ").strip()
                if opt == '1':
                    show_portfolio_positions()
                elif opt == '2':
                    show_portfolio_metrics_cli()
                elif opt == '3':
                    show_portfolio_valuation_tree()
                elif opt == '4':
                    break
                else:
                    print("[ERROR] Opción no válida.")
                    
        elif choice == '7':
            while True:
                print("\n--- CATEGORÍA: HISTÓRICO ---")
                print("1. Mostrar historial completo de movimientos (LinkedList)")
                print("2. Ejecutar Demos y simulaciones originales")
                print("3. Volver al menú principal")
                opt = input("Seleccione una opción: ").strip()
                if opt == '1':
                    show_portfolio_movements()
                elif opt == '2':
                    print("\n--- EJECUTANDO DEMOS ORIGINALES ---")
                    run_database_etl_demo()
                    run_portfolio_simulation()
                    run_relationship_graph_demo()
                elif opt == '3':
                    break
                else:
                    print("[ERROR] Opción no válida.")
                    
        elif choice == '8':
            print("\nGracias por utilizar Investor Scout. ¡Hasta pronto!")
            sys.exit(0)
        else:
            print("[ERROR] Opción no válida. Intente de nuevo.")

if __name__ == "__main__":
    main_menu()
