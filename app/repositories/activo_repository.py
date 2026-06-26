from typing import Optional
from app.repositories.base_repository import BaseRepository
from app.models.domain import Asset

class ActivoRepository(BaseRepository):
    """
    Repository for the 'activo' table.
    """
    def save(self, asset: Asset) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO activo (ticker, nombre, tipo_activo, moneda, exchange, pais)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    nombre = VALUES(nombre),
                    tipo_activo = VALUES(tipo_activo),
                    moneda = VALUES(moneda),
                    exchange = VALUES(exchange),
                    pais = VALUES(pais)
            """
            cursor.execute(query, (
                asset.ticker,
                asset.nombre,
                asset.tipo_activo,
                asset.moneda,
                asset.exchange,
                asset.pais
            ))
            conn.commit()
            
            # Fetch the generated or existing id
            cursor.execute("SELECT id_activo FROM activo WHERE ticker = %s", (asset.ticker,))
            res = cursor.fetchone()
            if res:
                asset.id_activo = res[0]
                return res[0]
            raise ValueError(f"Could not retrieve id_activo for ticker {asset.ticker}")
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_by_ticker(self, ticker: str) -> Optional[Asset]:
        ticker = ticker.upper()
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id_activo, ticker, nombre, tipo_activo, moneda, exchange, pais FROM activo WHERE ticker = %s"
            cursor.execute(query, (ticker,))
            row = cursor.fetchone()
            if row:
                return Asset(
                    id_activo=row["id_activo"],
                    ticker=row["ticker"],
                    nombre=row["nombre"],
                    tipo_activo=row["tipo_activo"],
                    moneda=row["moneda"],
                    exchange=row["exchange"],
                    pais=row["pais"]
                )
            return None
        finally:
            cursor.close()
            self.close_connection(conn)
