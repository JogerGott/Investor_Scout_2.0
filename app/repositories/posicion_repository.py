from typing import List, Optional
from app.repositories.base_repository import BaseRepository
from app.models.holding import Holding

class PosicionRepository(BaseRepository):
    """
    Repository for the 'posicion' table in MySQL.
    """
    def save(self, id_portafolio: int, id_activo: int, shares: float, avg_cost: float, market_value: Optional[float] = None, unrealized_pnl: Optional[float] = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO posicion (id_portafolio, id_activo, posicion_actual, costo_base, valor_mercado, unrealized_pnl)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    posicion_actual = VALUES(posicion_actual),
                    costo_base = VALUES(costo_base),
                    valor_mercado = VALUES(valor_mercado),
                    unrealized_pnl = VALUES(unrealized_pnl)
            """
            cursor.execute(query, (
                id_portafolio,
                id_activo,
                shares,
                avg_cost,
                market_value,
                unrealized_pnl
            ))
            conn.commit()
        finally:
            cursor.close()
            self.close_connection(conn)

    def delete(self, id_portafolio: int, id_activo: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = "DELETE FROM posicion WHERE id_portafolio = %s AND id_activo = %s"
            cursor.execute(query, (id_portafolio, id_activo))
            conn.commit()
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_all_by_portafolio(self, id_portafolio: int) -> List[Holding]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
                SELECT p.id_activo, a.ticker, p.posicion_actual, p.costo_base, p.valor_mercado, p.unrealized_pnl
                FROM posicion p
                JOIN activo a ON p.id_activo = a.id_activo
                WHERE p.id_portafolio = %s
            """
            cursor.execute(query, (id_portafolio,))
            rows = cursor.fetchall()
            holdings = []
            for row in rows:
                holding = Holding(
                    ticker=row["ticker"],
                    shares=float(row["posicion_actual"]),
                    avg_cost=float(row["costo_base"])
                )
                holding.current_value = float(row["valor_mercado"]) if row["valor_mercado"] is not None else 0.0
                holding.id_activo = row["id_activo"]  # Dynamically add ID
                holdings.append(holding)
            return holdings
        finally:
            cursor.close()
            self.close_connection(conn)
