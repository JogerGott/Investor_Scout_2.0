from typing import Optional
from datetime import date
from app.repositories.base_repository import BaseRepository
from app.models.domain import MarketMetrics

class MetricsRepository(BaseRepository):
    """
    Repository for the 'metricas_mercado' table.
    """
    def save(self, metrics: MarketMetrics):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO metricas_mercado (id_activo, fecha, precio, market_cap, enterprise_value, pe_ratio, pe_forward, pb_ratio, ps_ratio, peg, beta, dividend_yield)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    precio = VALUES(precio),
                    market_cap = VALUES(market_cap),
                    enterprise_value = VALUES(enterprise_value),
                    pe_ratio = VALUES(pe_ratio),
                    pe_forward = VALUES(pe_forward),
                    pb_ratio = VALUES(pb_ratio),
                    ps_ratio = VALUES(ps_ratio),
                    peg = VALUES(peg),
                    beta = VALUES(beta),
                    dividend_yield = VALUES(dividend_yield)
            """
            cursor.execute(query, (
                metrics.id_activo,
                metrics.fecha,
                metrics.precio,
                metrics.market_cap,
                metrics.enterprise_value,
                metrics.pe_ratio,
                metrics.pe_forward,
                metrics.pb_ratio,
                metrics.ps_ratio,
                metrics.peg,
                metrics.beta,
                metrics.dividend_yield
            ))
            conn.commit()
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_latest(self, id_activo: int) -> Optional[MarketMetrics]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
                SELECT id_metricas, id_activo, fecha, precio, market_cap, enterprise_value, pe_ratio, pe_forward, pb_ratio, ps_ratio, peg, beta, dividend_yield
                FROM metricas_mercado 
                WHERE id_activo = %s 
                ORDER BY fecha DESC LIMIT 1
            """
            cursor.execute(query, (id_activo,))
            row = cursor.fetchone()
            if row:
                return self._map_row(row)
            return None
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_by_date(self, id_activo: int, fecha: date) -> Optional[MarketMetrics]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
                SELECT id_metricas, id_activo, fecha, precio, market_cap, enterprise_value, pe_ratio, pe_forward, pb_ratio, ps_ratio, peg, beta, dividend_yield
                FROM metricas_mercado 
                WHERE id_activo = %s AND fecha = %s
            """
            cursor.execute(query, (id_activo, fecha))
            row = cursor.fetchone()
            if row:
                return self._map_row(row)
            return None
        finally:
            cursor.close()
            self.close_connection(conn)

    def _map_row(self, row: dict) -> MarketMetrics:
        return MarketMetrics(
            id_metricas=row["id_metricas"],
            id_activo=row["id_activo"],
            fecha=row["fecha"],
            precio=float(row["precio"]) if row["precio"] else None,
            market_cap=row["market_cap"],
            enterprise_value=row["enterprise_value"],
            pe_ratio=float(row["pe_ratio"]) if row["pe_ratio"] else None,
            pe_forward=float(row["pe_forward"]) if row["pe_forward"] else None,
            pb_ratio=float(row["pb_ratio"]) if row["pb_ratio"] else None,
            ps_ratio=float(row["ps_ratio"]) if row["ps_ratio"] else None,
            peg=float(row["peg"]) if row["peg"] else None,
            beta=float(row["beta"]) if row["beta"] else None,
            dividend_yield=float(row["dividend_yield"]) if row["dividend_yield"] else None
        )
