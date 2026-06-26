from typing import List, Optional
from datetime import date
from app.repositories.base_repository import BaseRepository
from app.models.domain import HistoricalPrice

class HistoricoRepository(BaseRepository):
    """
    Repository for the 'historico' table.
    """
    def save_bulk(self, prices: List[HistoricalPrice]):
        """
        Saves a list of historical prices in bulk using ON DUPLICATE KEY UPDATE.
        """
        if not prices:
            return
            
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO historico (id_activo, fecha, open_price, high_price, low_price, close_price, adjust_close, volumen)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    open_price = VALUES(open_price),
                    high_price = VALUES(high_price),
                    low_price = VALUES(low_price),
                    close_price = VALUES(close_price),
                    adjust_close = VALUES(adjust_close),
                    volumen = VALUES(volumen)
            """
            data = [
                (
                    p.id_activo,
                    p.fecha,
                    p.open_price,
                    p.high_price,
                    p.low_price,
                    p.close_price,
                    p.adjust_close,
                    p.volumen
                )
                for p in prices
            ]
            cursor.executemany(query, data)
            conn.commit()
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_prices(self, id_activo: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[HistoricalPrice]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id_activo, fecha, open_price, high_price, low_price, close_price, adjust_close, volumen FROM historico WHERE id_activo = %s"
            params = [id_activo]
            if start_date:
                query += " AND fecha >= %s"
                params.append(start_date)
            if end_date:
                query += " AND fecha <= %s"
                params.append(end_date)
            query += " ORDER BY fecha ASC"
            
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            return [
                HistoricalPrice(
                    id_activo=row["id_activo"],
                    fecha=row["fecha"],
                    open_price=float(row["open_price"]) if row["open_price"] else None,
                    high_price=float(row["high_price"]) if row["high_price"] else None,
                    low_price=float(row["low_price"]) if row["low_price"] else None,
                    close_price=float(row["close_price"]),
                    adjust_close=float(row["adjust_close"]),
                    volumen=row["volumen"]
                )
                for row in rows
            ]
        finally:
            cursor.close()
            self.close_connection(conn)
