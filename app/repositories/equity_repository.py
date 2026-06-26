from typing import Optional
from app.repositories.base_repository import BaseRepository
from app.models.domain import EquityDetails

class EquityRepository(BaseRepository):
    """
    Repository for the 'equity' table.
    """
    def save(self, details: EquityDetails):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO equity (id_activo, sector, industria, earnings_date)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    sector = VALUES(sector),
                    industria = VALUES(industria),
                    earnings_date = VALUES(earnings_date)
            """
            cursor.execute(query, (
                details.id_activo,
                details.sector,
                details.industria,
                details.earnings_date
            ))
            conn.commit()
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_by_id(self, id_activo: int) -> Optional[EquityDetails]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id_activo, sector, industria, earnings_date FROM equity WHERE id_activo = %s"
            cursor.execute(query, (id_activo,))
            row = cursor.fetchone()
            if row:
                return EquityDetails(
                    id_activo=row["id_activo"],
                    sector=row["sector"],
                    industria=row["industria"],
                    earnings_date=row["earnings_date"]
                )
            return None
        finally:
            cursor.close()
            self.close_connection(conn)
